import dataframe_image as dfi

def convet_dataframe_to_png(df):
    dfi.export(df, 'static/temp.png')
    png = open('static/temp.png', 'rb')

    return png



 

