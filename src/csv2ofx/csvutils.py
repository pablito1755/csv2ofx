

from datetime import datetime
import csv

from wx.grid import PyGridTableBase


class SimpleCSVGrid(PyGridTableBase):
    """
        A very basic instance that allows the csv contents to be used
        in a wx.Grid
    """
    def __init__(self,csv_path,mapping,delimiter=',',skip_last=0):
        PyGridTableBase.__init__(self)
        # delimiter, quote could come from config file perhaps
        csv_reader = csv.reader(open(csv_path,'r'),delimiter=delimiter,quotechar='"')
        self.grid_contents = [row for row in csv_reader if len(row)>0]
        if skip_last:
            self.grid_contents=self.grid_contents[:-skip_last]
        
        # the 1st row is the column headers
        self.grid_cols = len(self.grid_contents[0])
        self.grid_rows = len(self.grid_contents)
                
        # header map
        # results in a dictionary of column labels to numeric column location            
        self.col_map=dict([(self.grid_contents[0][c],c) for c in range(self.grid_cols)])
        
        self.mapping = mapping
        self.date_column = self.GetColPos(self.mapping['_params']['Header_TransactionDate'])
        self.min_datetime = None
        self.max_datetime = None
        self.TransIdPrefix = None

        
    def GetMinDate(self):
        if self.min_datetime == None:
            self.min_datetime = datetime.max
            for row in range(self.GetNumberRows()):
                tmpDatetime = self.GetDatetime(row)
                if tmpDatetime < self.min_datetime:
                    self.min_datetime = tmpDatetime
        return self.min_datetime     
            
    def GetMaxDate(self):
        if self.max_datetime == None:
            self.max_datetime = datetime.min
            for row in range(self.GetNumberRows()):
                tmpDatetime = self.GetDatetime(row)
                if tmpDatetime > self.max_datetime:
                    self.max_datetime = tmpDatetime
        return self.max_datetime
    
    def GetDatetime(self, row):
        return self.mapping['_params']['Function_DateStrToDatetime'](self.GetValue(row, self.date_column))
        
    def GenerateTransactionId(self, row):
        if self.TransIdPrefix == None:
            self.TransIdPrefix = self.GetMinDate().strftime('%Y%m%d') + ':' + self.GetMaxDate().strftime('%Y%m%d')           
        return self.TransIdPrefix  + ':' + str(row)
            
    def GetNumberRows(self):
        return self.grid_rows-1
    
    def GetNumberCols(self):
        return self.grid_cols
    
    def IsEmptyCell(self,row,col):
        return len(self.grid_contents[row+1][col]) == 0
    
    def GetValue(self,row,col):
        return self.grid_contents[row+1][col]
    
    def GetColLabelValue(self,col):
        return self.grid_contents[0][col]
    
    def GetColPos(self,col_name):
        return self.col_map[col_name]
    


def xmlize(dat):
    """
        Xml data can't contain &,<,>
        replace with &amp; &lt; &gt;
        Get newlines while we're at it.
    """
    return dat.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('\r\n',' ').replace('\n',' ')
    
def fromCSVCol(row,grid,col_name):
    """
        Uses the current row and the name of the column to look up the value from the csv data.
    """
    return xmlize(grid.GetValue(row,grid.GetColPos(col_name)))
    
def inverseSign(v):
    f = float(v)
    inv = f * -1
    return "%.2f" % inv
