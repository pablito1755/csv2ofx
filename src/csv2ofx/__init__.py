
import sys, os, time
from traceback import print_exc

import wx
from wx import xrc
import wx.grid as grd

from csvutils import *
import ofx, qif


        


class csv2ofx(wx.App):
    """
        class csv2ofx
        
        Extends wx.App
        
        Provides a data table to preview csv input.
    """
    def __init__(self):
        wx.App.__init__(self,redirect=False)
    
    def OnInit(self):
        """
           Initializes and shows frame from csv2ofx.xrc 
        """
        
        # load the xml resource
        script_dir = os.path.dirname ( __file__ )
        self.res = xrc.XmlResource ( "%s/csv2ofx.xrc" % script_dir )
        
        # load the frame from the resource        
        self.frame = self.res.LoadFrame ( None, "ID_CSV2OFX")
        
        # associate the MenuBar
        self.frame.SetMenuBar (
            self.res.LoadMenuBar("ID_MENUBAR")
        )

        # the grid
        self.grid = xrc.XRCCTRL(self.frame,"ID_GRID")
        self.grid.EnableEditing(False)
        
        # the mappings
        self.mappings = xrc.XRCCTRL(self.frame,"ID_MAPPINGS")

        try:
            try:
              #  try current directory first
              if os.path.isfile ( 'csv2ofx_custom.py' ):
                execfile ( 'csv2ofx_custom.py', globals())
                for mapping in all_mappings:
                    self.mappings.Append ( mapping, all_mappings[mapping] )
              else:
                raise # try the home directory
            except:
                homepath=os.path.expanduser('~')
                cust_mappings = "%s/csv2ofx_custom.py" % homepath
                if os.path.isfile( cust_mappings ):
                    execfile ( cust_mappings, globals() )
                    for mapping in all_mappings:
                        self.mappings.Append ( mapping, all_mappings[mapping] )
        except: 
            print_exc()
            # Use built in mappings as default/backup
        if self.mappings.IsEmpty():
            print "Using Default Mappings"
            import mappings
            for mapping in mappings.all_mappings:
                self.mappings.Append ( mapping, mappings.all_mappings[mapping] )
        self.mappings.SetSelection(0)

        # output formats
        self.exports = xrc.XRCCTRL(self.frame,"ID_EXPORT")
        
        # handle events
        self.Bind ( wx.EVT_MENU, self.OnCloseBtn, id=xrc.XRCID("ID_MENU_CLOSE"))
        self.Bind ( wx.EVT_BUTTON, self.OnCloseBtn, id=xrc.XRCID("ID_BTN_CLOSE"))
        self.Bind ( wx.EVT_MENU, self.OnImport, id=xrc.XRCID("ID_MENU_IMPORT"))
        self.Bind ( wx.EVT_BUTTON, self.OnImport, id=xrc.XRCID("ID_BTN_IMPORT"))
        self.Bind ( wx.EVT_MENU, self.OnExport, id=xrc.XRCID("ID_MENU_EXPORT"))
        self.Bind ( wx.EVT_BUTTON, self.OnExport, id=xrc.XRCID("ID_BTN_EXPORT"))
        self.frame.Bind ( wx.EVT_CLOSE, self.OnClose )
        self.frame.Bind ( wx.EVT_MOVE, self.OnMove )
        self.frame.Bind ( wx.EVT_SIZE, self.OnSize )
        
        
        # app preferences
        self.config = wx.Config ( "csv2ofx" )

        x=self.config.ReadInt("screenx",100)
        y=self.config.ReadInt("screeny",100)
        w=self.config.ReadInt("screenw",600)
        h=self.config.ReadInt("screenh",550)

        
        # show the frame        
        self.SetTopWindow(self.frame)
        
        self.frame.SetPosition( (x,y) )
        self.frame.SetSize( (w,h) )
        self.frame.Show()
        return True
        
    def OnCloseBtn(self,evt):
        """
            Close the application.
        """
        self.frame.Close()
        
    def OnClose(self,evt):
        """
            Appliction Closing
        """
        print "GoodBye"
        self.config.Flush()
        evt.Skip()
        
    def OnMove(self,evt):
        """
            Application Screen Position Changed
        """
        x,y = evt.GetPosition()
        self.config.WriteInt("screenx",x)
        self.config.WriteInt("screeny",y)
        evt.Skip()
        
    def OnSize(self,evt):
        """
            Application Size Changed
        """
        w,h = evt.GetSize()
        self.config.WriteInt("screenw",w)
        self.config.WriteInt("screenh",h)
        evt.Skip()
        
    def OnImport(self,evt):
        """
            Import a csv file.
        """
        
        # create an open file dialog
        dlg = wx.FileDialog (
            self.frame,
            message="Open CSV File",
            wildcard="CSV Files (*.csv)|*.csv|All Files (*.*)|*.*",
            style=wx.OPEN|wx.CHANGE_DIR,            
        )
        if dlg.ShowModal() == wx.ID_OK:
            path=dlg.GetPath()
            self._open_file(path)
        dlg.Destroy()
    
    
    def _open_file(self,path):
        """
            Opens a csv file and loads it's contents into the data table.
            
            path: path to the csv file.
        """
        
        print "Open File %s" % path
                      
        mapping = self.mappings.GetClientData(self.mappings.GetSelection())
        try:
            delimiter=mapping['_params']['delimiter']
        except:
            delimiter=','
        try:
            skip_last=mapping['_params']['skip_last']
        except:
            skip_last=0
        self.grid_table = SimpleCSVGrid(path,mapping,delimiter,skip_last)
        self.grid.SetTable(self.grid_table)
        self.opened_path = path
        
    def OnExport(self,evt):
        if not hasattr(self,'grid_table'):
            wx.MessageDialog(
                self.frame,
                "Use import to load a csv file.",
                "No CSV File loaded.",
                wx.OK|wx.ICON_ERROR                
            ).ShowModal()
            return
        
        format = self.exports.GetStringSelection()
        dlg = wx.FileDialog(
            self.frame,
            message='Export File',
            wildcard="QIF Files (*.qif)|*.qif|OFX Files (*.ofx)|*.ofx|All Files (*.*)|*.*", 
            style=wx.SAVE|wx.CHANGE_DIR,
	    defaultDir=os.path.dirname(self.opened_path),
            defaultFile=os.path.basename(self.opened_path).replace('csv',format.lower()) 
        )
        dlg.SetFilterIndex( format=="OFX" and 1 or 0 )
        path=None
        try:
            if dlg.ShowModal() == wx.ID_OK:
                path=dlg.GetPath()
            else:
                return
        finally:
            dlg.Destroy();

        try:
            maptype=self.mappings.GetClientData(self.mappings.GetSelection())['_params']['maptype']
        except:
            maptype='bank'
            
        mapping=self.mappings.GetClientData(self.mappings.GetSelection())[format]
        grid=self.grid_table
        
        if format == 'OFX':
            csv2ofx_export = ofx.export
        elif format == 'QIF':
            csv2ofx_export = qif.export
        else:
            raise Exception ( "Unhandled export format: %s" % format )
        csv2ofx_export(path,mapping,maptype,grid)
        wx.MessageDialog (
            self.frame,
            "%s file saved at:\n%s" % ( format, path ),
            "Export Complete",
            wx.OK|wx.ICON_INFORMATION
        ).ShowModal()


