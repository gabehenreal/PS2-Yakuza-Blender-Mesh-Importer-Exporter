from .binary_reader import BinaryReader 

def read_txb_info(filepath,TXB_filename,TXB_fileformat):
    
    f = open(filepath, 'rb')
    reader = BinaryReader(f.read())
    
    # check if its a txb file
    if reader.read_str(4) != 'TXBP':
        self.report({'ERROR'}, "Invalid file magic!")
        raise Exception("Breaking op, file has invalid magic")
    else:
        print("File is valid")
        
    # get txb image counts:
    reader.seek(4,0)
    imagecounts = reader.read_uint32()
    
    # get ids 
    imageids =[]   
    imagenames = []
    skip = 0
    for i in range(imagecounts):
        reader.seek(32 + skip,0)
        blocksize = reader.read_uint32()
        reader.seek(32 + skip + 24,0)
        
        imgid = reader.read_uint32() 
        imageids.append(imgid)        
        print(blocksize,imgid,skip)
        
        newimagename = TXB_filename+str(i)+TXB_fileformat
        imagenames.append(newimagename)
        newval = blocksize+32
        skip += newval    
    f.close()
  
    return imageids,imagenames