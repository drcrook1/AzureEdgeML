#
# @Author: DaCrook
# This code simply uploads image data we already have into the appropriate location in blob
# We also go ahead and upload a meta file for class + file
#

from azure.storage.blob import BlockBlobService
import os
from scipy import misc
import imageio

base_dir = 'C:/Users/DrCrook/Documents/AzureML/ClassifyOfficeItems/images/'
account = 'iotmlreceiving'
account_key = 'Rg/wEKqkhPAso5FqvgtAQrYBP0dTFcYQc35LhZRvNBEUQE8y7HXf+MAd9rUrk2lSR4eqSZULOAvDZ1YFItg4RA=='

bbs = BlockBlobService(account_name = account, account_key = account_key)

for dirName, subDirList, files in os.walk(base_dir):
    #Make sure we have a container for each image class
    for dir in subDirList:
        bbs.create_container(dir)
    
    #Upload images to appropriate container
    for file in files:
        cont = dirName.split('/')[-1]
        full_path = dirName + '/' + file
        print(full_path)
        image = misc.imread(full_path)
        os.remove(full_path)
        imageio.imwrite(full_path[0:-4] + '.jpg', image)
        bbs.create_blob_from_path(
            cont,
            file.replace(' ', ''),
            dirName + '/' + file
        )

