#GUI back end
import PySimpleGUI as sg
import os.path
import io
import numpy as np
from PIL import Image
from skimage import io as skio
from skimage.morphology import remove_small_objects, skeletonize, closing, disk
from skimage.filters import sobel
from skimage.color import rgb2gray, grey2rgb

def display_image(fig):
    '''
    Will convert skimage array into resized PIL object so that it can be displayed in tkinter
    '''
    img = Image.fromarray(fig)

    cur_width, cur_height = img.size

    new_width, new_height = 1280, 720
    scale = min(new_height/cur_height, new_width/cur_width)
    img = img.resize((int(cur_width*scale), int(cur_height*scale)), Image.ANTIALIAS)

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img

    window['-IMAGE-'].update(data = bio.getvalue())

def dot(fig, y, x, rad):
    '''
    Creates a blue dot if possible
    '''
    for a in range(rad):
        for b in range(rad):
            try:
                fig[y-(rad//2)+a][x-(rad//2)+b] = [0, 0, 255]
            except:
                pass

def create_image():
    '''
    This function runs all the image analysis as detailed in the 'Linear intercept method v2' notebook
    All changes made at each stage will be shown in a different colour
    '''

    fig = skio.imread(filename)
    y, x = np.shape(fig)[:2]

    if len(np.shape(fig)) == 2:
        fig = grey2rgb(fig)
        fig = 1 - fig
        fig = np.array(fig*255, dtype=np.uint8)     

    if values['-STAGE-'] == 1:
        display_image(fig)
        return

    #threshold - greyscale, intensity map, threshold
    tfig = sobel(rgb2gray(fig)) > float(values['-THRESH-'])

    if values['-STAGE-'] == 2:
        dfig = np.zeros([y, x, 4], dtype=np.uint8)
        dfig[:,:,:3] = fig
        dfig[:,:,3] = 180
        dfig[tfig==1] = [255, 0, 0, 255]
        display_image(dfig)
        return

    #artifacts - closing grain boandaries, remove small objects and skeletonize
    afig = closing(tfig, disk(3))
    afig = remove_small_objects(afig, min_size=int(values['-ARTS-']))
    afig = skeletonize(afig)

    if values['-STAGE-'] == 3:
        dfig = np.zeros([y, x, 3], dtype=np.uint8)
        dfig[tfig==1] = [255, 0, 0]
        dfig[afig==1] = [255, 255, 255]
        display_image(dfig)
        return

    #intercepts - create intercept lines, count transitions along lines, and return grain size
    sep = int(values['-SEP-'])
    rx, ry = range(0, x, sep)[1:], range(0, y, sep)[1:]
    xcount, ycount = [], []
    counter = 0

    if values['-STAGE-'] == 4:
        ifig = grey2rgb(afig)
        ifig = np.array(ifig*255, dtype='int')

    elif values['-STAGE-'] == 5:
        ifig = fig

    for j in ry: #creting horizontal red intercepts
        ifig[j] = [[255,0,0] for i in range(x)]

    for i in rx: #creating vertical red intercepts
        for j in range(y):
            ifig[j][i] = [255,0,0]

    for j in ry: # finding incercepts on vertical lines
        
        for i in range(x):
            if [afig[j][i-1], afig[j][i]]  == [0, 1]:
                counter += 1
                dot(ifig, j, i, 5)
        
        try:
            xcount += [x / counter]
            counter = 0
        except:
            window['-RES-'].update('Not enought data!')
            return

    for i in rx: #finding intercepts on horizontal lines

        for j in range(y):    
            if [afig[j-1][i], afig[j][i]]  == [0, 1]:
                counter += 1
                dot(ifig, j, i, 5)
        
        try:
            ycount += [y / counter]
            counter = 0
        except:
            window['-RES-'].update('Not enought data!')
            return

    ifig = np.array(ifig, dtype=np.uint8)

    display_image(ifig)

    grain_size = ( np.mean(xcount)*len(rx) + np.mean(ycount)*len(ry) ) / ( len(ry) + len(rx) )

    window['-RES-'].update('Average grainsize is {} pixels'.format(str(int(grain_size))))


#GUI layout
sg.theme('DarkBrown4')

lcol = [

    [sg.Frame('Stage', layout=[
        [sg.Slider((1, 5), default_value=1, orientation='horizontal', disable_number_display=True, key='-STAGE-',
            enable_events=True, size=(35.3, 20), pad=(10,5))],
        [sg.Text('Image{0}Threshold{0}Artifacts{0}Intercepts{0}Result'.format(" "*5))]])],

    [sg.Frame('Select Images', layout=[
        [sg.Text('Folder'), sg.In(size=(30,1), enable_events=True ,key='-FOLDER-'), sg.FolderBrowse()],
        [sg.Listbox(values=[r'Coloured Test.jpg', r'Grey Test.png'],
            enable_events=True, size=(44, 10), key='-FILE LIST-')]])],

    [sg.Frame('Magnification', layout=[
        [sg.Text('This is the length of the scalebar in pixels / metre')],
        [sg.Button('Calculate', key='-CALC-'), sg.Input(default_text='100', size=(5,1), enable_events=True, key='-MAG-', pad=((215,10), (0,0)))]])],

    [sg.Frame('Threshold', layout=[
        [sg.Text('The minimum greyscale value of the grain boundaries')],
        [sg.Slider((0.0, 0.5), default_value=0.25, resolution=0.001, orientation='horizontal', disable_number_display=True, size=(30,20), enable_events=True, key='-TSLIDER-'),
            sg.Input(default_text='0.25', size=(5,1), enable_events=True, pad=((10,10), (0,0)), key='-THRESH-')]])],

    [sg.Frame('Artifacts', layout=[
        [sg.Text('Maximum size in pixels of artifacts to be removed')],
        [sg.Slider((0, 500), default_value=300, resolution=5, orientation='horizontal', disable_number_display=True, size=(30,20), enable_events=True, key='-ASLIDER-'),
            sg.Input(default_text='300', size=(5,1), enable_events=True, pad=((10,10), (0,0)), key='-ARTS-')]])],

    [sg.Frame('Seperation', layout=[
        [sg.Text('Distance in pixels between red intercept lines')],
        [sg.Slider((10, 200), default_value=100, resolution=10, orientation='horizontal', disable_number_display=True, size=(30,20), enable_events=True, key='-SSLIDER-'),
            sg.Input(default_text='100', size=(5,1), enable_events=True, pad=((10,10), (0,0)), key='-SEP-')]])],

    [sg.Frame('Results', layout=[
        [sg.Column([[sg.Text('Average grainsize is not yet calculated', key='-RES-')]], size=(340, 30), pad=(0,0))]])],
    
    [sg.Text('Made by Ayham Al-Saffar. Check out my GitHub for more!', text_color='grey')]
]

img = sg.Image(r'New Logo.png', key='-IMAGE-')

layout = [[sg.Column(lcol, justification='left'), img]]

window = sg.Window('Grainsizer X', layout)

filename = None

#GUI logic
while True:  # Event Loop
    event, values = window.read()
    #print(event, values)

    if event == sg.WIN_CLOSED or event in ('Close', None):
        break

    if event == '-STAGE-':
        if filename:
            create_image()
        else:
            sg.popup('Please select an image before beginning analysis', title='Error',
                auto_close=True, auto_close_duration=3)
            window['-STAGE-'].update(1)
            values['-STAGE-'] = 1

    if event == '-FOLDER-':
        folder = values['-FOLDER-']
        
        try:
            file_list = os.listdir(folder)         # get list of files in folder
        
        except:
            file_list = []
        fnames = [f for f in file_list if os.path.isfile(
            os.path.join(folder, f)) and f.lower().endswith((".png", ".jpg", "jpeg", ".tiff", ".bmp"))]
        window['-FILE LIST-'].update(fnames)

    elif event == '-FILE LIST-':    # A file was chosen from the listbox
        try:
            filename = os.path.join(values['-FOLDER-'], values['-FILE LIST-'][0])
            window['-STAGE-'].update(1)
            create_image()

        except Exception as E:
            print(f'** Error {E} **')
            pass        # something weird happened making the full filename
    
    if event == '-CALC-':
        sg.popup('Sorry this feature has not yet been implemented', title='Error',
            auto_close=True, auto_close_duration=3)

    if event == '-TSLIDER-' or event == '-THRESH-':

        if event == '-TSLIDER-':
            window['-THRESH-'].update(float(values['-TSLIDER-']))
            values['-THRESH-'] = float(values['-TSLIDER-'])

        if event == '-THRESH-':
            window['-TSLIDER-'].update(float(values['-THRESH-']))
            values['-TSLIDER-'] = float(values['-THRESH-'])

        create_image()

    if event == '-ASLIDER-' or event == '-ARTS-':

        if event == '-ASLIDER-':
            window['-ARTS-'].update(int(values['-ASLIDER-']))
            values['-ARTS-'] = int(values['-ASLIDER-'])

        if event == '-ARTS-':
            window['-ASLIDER-'].update(int(values['-ARTS-']))
            values['-ASLIDER-'] = int(values['-ARTS-'])

        create_image()
        
    if event == '-SSLIDER-' or event == '-SEP-':

        if event == '-SSLIDER-':
            window['-SEP-'].update(int(values['-SSLIDER-']))
            values['-SEP-'] = int(values['-SSLIDER-'])

        if event == '-SEP-':
            window['-SSLIDER-'].update(int(values['-SEP-']))
            values['-SSLIDER-'] = int(values['-SEP-'])

        create_image()

window.close()