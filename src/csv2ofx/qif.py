

def export ( path, mapping, maptype, grid ):
    """
        path: file path to save file
        mapping: mapping for grid data
        grid: csv data
    """


    accounts={}
    cur_parent = None
    for row in range(grid.GetNumberRows()):
        tran = dict( [ (k, mapping[k](row,grid) ) for k in ('Date', 'Payee', 'Memo', 'Category', 'Class', 'Amount', 'Number' )] )
        if not mapping['split'](row,grid):
            acct = accounts.setdefault(mapping['Account'](row,grid),{})
            acct['Account'] = mapping['Account'](row,grid)
            acct['AccountDscr'] = mapping['AccountDscr'](row,grid)
            trans = acct.setdefault('trans',[]) 
            trans.append(tran)
            cur_parent = tran
        else:
            splits = cur_parent.setdefault('splits',[])
            splits.append(tran)


    if maptype=='creditcard':
        header_type = 'CCard'
    else:
        header_type = 'Bank'
        
    o=open(path,'w')
    for a in accounts.values():
        o.write("!Account\nN%(Account)s\nD%(AccountDscr)s\n^\n" % a)
        o.write("!Type:%s\n" % header_type)
        for t in a['trans']:
            o.write("D%(Date)s\nT%(Amount)s\nP%(Payee)s\nM%(Memo)s\nL%(Category)s/%(Class)s\n" % t )
            for s in t.get('splits',[]):
                o.write("S%(Category)s/%(Class)s\nE%(Memo)s\n$%(Amount)s\n" % s )
            o.write("^\n")

    o.close()
