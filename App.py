#GUI back end
import PySimpleGUI as sg
import tkinter as tk
import os.path
import io
import numpy as np
from PIL import Image, ImageTk
from skimage import io as skio
from skimage.morphology import remove_small_objects, skeletonize, closing, disk
from skimage.filters import sobel
from skimage.color import rgb2gray, grey2rgb

def resource_path(relative_path):
    '''
    *** Only used when creating .exe file with pyinstaller ***
    Get file path of resources after they are packed into the .exe
    '''
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def dot(fig, y, x, rad):
    '''
    Creates a blue dot
    '''
    fig[y-(rad//2) : y+(rad//2)+1, x-(rad//2) : x+(rad//2)+1] = [0, 0, 255]

def open_fig():
    '''
    Opens and formats the currently selected file into an array (fig)
    '''
    fig = skio.imread(filename)
    image_height, image_length = np.shape(fig)[:2]

    if len(np.shape(fig)) == 2: #if image is in greyscale
        fig = 1 - grey2rgb(fig)
        fig = fig*255
    
    if len(np.shape(fig)) == 4: #if image has a transparency layer
        fig = fig[:,:,:3]

    fig = np.array(fig, dtype=np.uint8)

    return fig, image_height, image_length

def mag_window():
    '''
    Creates popup window to find magnification of the figure in pixels / metre
    and the coordinates of the scale bar so it can be ignored in analysis
    '''
    sg.theme('DarkBrown4')

    scale_bar = sg.Column([[sg.Frame('Scale Bar', layout=[
        [sg.Text('This area will be ignored during analysis')],
        [sg.Button('Draw', key='-SCALEBAR-'), sg.Input('Scalebar Coordinates', key='-SBCOORDS-',
            size=(20, 1), pad=((60, 5), (0, 0)))]
    ])]], size=(280, 85), pad=((0,0), (0,0)), element_justification = 'right')

    scale_length = sg.Column([[sg.Frame('Scale Length', layout=[
        [sg.Text('The true length of the scale line')],
        [sg.Input('', key='-LEN-', size=(10, 1), pad=((30,5),(7,5))),
            sg.Combo(['mm', 'μm', 'nm'], key='-UNIT-', pad=((5,30),(7,5)), size=(5, 1))]
    ])]], size=(220, 85), pad=((0,0), (0,0)),  element_justification = 'center')
    
    scale_line = sg.Column([[sg.Frame('Scale Line', layout=[
        [sg.Text('Length of the scale line in pixels')],
        [sg.Button('Draw', key='-SCALE-'), sg.Input('scale line length', key='-SLLEN-',
            size=(20, 1), pad=((60, 5), (0, 0)))]
    ])]], size=(280, 85), pad=((0,0), (0,0)),  element_justification = 'left')

    layout = [
        [sg.Graph(canvas_size=(800, 450), graph_bottom_left=(0, image_height), graph_top_right=(image_length, 0),
            key="-GRAPH-", enable_events=True, background_color='white', drag_submits=True)],

        [scale_bar, scale_length, scale_line],

        [sg.Button('Done', key='-DONE-', pad=(0, 5))]
    ]

    window = sg.Window("Magnification Finder", layout, finalize=True, element_justification='centre')

    # get the graph element for ease of use later
    graph = window["-GRAPH-"]
    
    #resizing fig to plot on graph
    img = Image.fromarray(fig)
    img = img.resize((800, 450), Image.ANTIALIAS)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    graph.draw_image(data = bio.getvalue(), location=(0,0))

    dragging = False
    start_point = end_point = prev_rect = None

    while True:
        event, values = window.read()
        print(event, values)

        if event == sg.WIN_CLOSED or event in ('Close', None):
            break

        if event == '-SCALEBAR-':
            
            if 'old_rect' in locals(): #if old_rect variable previously created
                graph.delete_figure(old_rect)

            dragging = False
            start_point = end_point = prev_rect = None

            while True:
                event, values = window.read()
                print(event, values)

                if event == "-GRAPH-":  # if there's a "Graph" event, then it's a mouse click
                    x, y = values["-GRAPH-"]

                    if not dragging:
                        start_point = (x, y)
                        dragging = True
                    
                    if prev_rect:
                        graph.delete_figure(prev_rect)
                    
                    end_point = (x, y)
                
                    prev_rect = graph.draw_rectangle(start_point, end_point, line_color='red')

                    window["-SBCOORDS-"].update(f"x:{x} y:{y}")

                if event == '-GRAPH-+UP':  # The right mouse button has been let go
                    window["-SBCOORDS-"].update(value=f"{start_point} to {end_point}")

                    #saving scalebar coords as y1, y2, x1, x2
                    sbcoords = [min(start_point[1], end_point[1]), max(start_point[1], end_point[1]),
                        min(start_point[0], end_point[0]), max(start_point[0], end_point[0])]

                    old_rect = prev_rect
                    start_point, end_point, prev_rect = None, None, None
                    dragging = False
                    break

        if event == '-SCALE-':
            
            if 'old_line' in locals(): #if old_line variable previously created
                graph.delete_figure(old_line)

            dragging = False
            start_point = end_point = prev_line = None

            while True:
                event, values = window.read()
                print(event, values)

                if event == "-GRAPH-":  # if there's a "Graph" event, then it's a mouse click
                    x, y = values["-GRAPH-"]

                    if not dragging:
                        start_point = (x, y)
                        dragging = True
                    
                    if prev_line:
                        graph.delete_figure(prev_line)
                    
                    end_point = (x, start_point[1])
                
                    prev_line = graph.draw_line(start_point, end_point, color='red', width=3)

                    window["-SLLEN-"].update(f"x:{x}")

                if event == '-GRAPH-+UP':  # The right mouse button has been let go
                    window["-SLLEN-"].update(value=f"{abs(start_point[0] - end_point[0])}")
                    old_line = prev_line
                    start_point, end_point, prev_line = None, None, None
                    dragging = False
                    break
        
        if event == '-DONE-':
            if values['-SBCOORDS-'] == 'Scalebar Coordinates' or values['-LEN-'] == '' or values['-UNIT-'] == '' or values['-SLLEN-'] == 'scale line length':
                sg.popup('Please input the relevant data before moving on', title='Error', auto_close=True, auto_close_duration=3)
            else:
                length = float(values['-LEN-']) / (1000 if values['-UNIT-'] == 'mm' else 1e6 if values['-UNIT-'] == 'μm' else 1e9)
                magnification = length / float(values['-SLLEN-']) 
                window.close()
                return sbcoords, magnification
                 
    window.close()

def threshold_fig():
    '''
    Thresholds the figure to find where the grain bounderies are (tfig)
    and creates a new figure highlighting the grain bounderies in red (dfig)
    '''
    tfig = sobel(rgb2gray(fig)) > float(values['-THRESH-'])

    if 'sbcoords' in globals(): #if the scalebar has been selected
        y1, y2, x1, x2 = sbcoords
        tfig[y1:y2+1, x1:x2+1] = False

    dfig = np.zeros([image_height, image_length, 4], dtype=np.uint8)
    dfig[:,:,:3] = fig
    dfig[:,:,3] = 120
    dfig[tfig==1] = [255, 0, 0, 255]

    return tfig, dfig

def artifact_fig():
    '''
    Removes small particles from the thresholded figures and skelotonizes
    the grain boundaries (afig). Creates a new figure (dfig) showing the 
    thresholded figure in white and the artifact free figure in red
    '''
    shape = disk(int(values['-GBWIDTH-']) + 2) #grain boundary width
    afig = closing(tfig, shape)
    afig = remove_small_objects(afig, min_size=int(values['-PARTICLES-']))
    afig = skeletonize(afig)

    dfig = np.zeros([image_height, image_length, 3], dtype=np.uint8)
    dfig[tfig==1] = [255, 0, 0]
    dfig[afig==1] = [255, 255, 255]
    
    return afig, dfig

def intercept_fig():
    '''
    Creates vertical and horizontal lines at regular intervals and
    counts the number of times a grain boundary intercepts one of these lines.
    This is used to work out the average grain size and a new figure showing
    these intercepts (ifig) is created
    '''
    sep = int(values['-SEP-'])
    rx, ry = range(0, image_length, sep)[1:], range(0, image_height, sep)[1:]
    counter = 0

    if values['-STAGE-'] == 4:
        ifig = grey2rgb(afig)
        ifig = np.array(ifig*255, dtype=np.uint8)

    elif values['-STAGE-'] == 5:
        ifig = np.array(fig)

    ifig[ry,:] = [255, 0, 0] 
    ifig[:, rx] = [255, 0, 0] 
    
    if 'sbcoords'  in globals(): #if the scalebar has  been selected
        y1, y2, x1, x2 = sbcoords

        if values['-STAGE-'] == 4:
            ifig[y1:y2+1, x1:x2+1] = 255 * grey2rgb(afig[y1:y2+1, x1:x2+1])
    
        elif values['-STAGE-'] == 5:
            ifig[y1:y2+1, x1:x2+1] = np.array(fig[y1:y2+1, x1:x2+1])

    #counting and marking intercepts
    counter += len([dot(ifig, j, i, 5) for j in ry for i in range(image_length)
        if [afig[j][i-1], afig[j][i]]  == [0, 1]])

    counter += len([dot(ifig, j, i, 5) for i in rx for j in range(image_height)
        if [afig[j-1][i], afig[j][i]]  == [0, 1]])
    
    line_len = image_height*len(rx) + image_length*len(ry)
    
    if 'sbcoords' in globals(): #if scalebar has been selected
        line_len -= (x2-x1) * len([i for i in ry if y1 <= i <= y2])
        line_len -= (y2-y1) * len([i for i in rx if x1 <= i <= x2])

    grain_size = line_len / counter 

    return ifig, grain_size

def display_image(fig):
    '''
    Will convert figure array into resized PIL object so that it can be displayed in the GUI window
    '''
    img = Image.fromarray(fig)

    cur_width, cur_height = img.size

    new_width, new_height = 1440, 810
    scale = min(new_height/cur_height, new_width/cur_width)
    img = img.resize((int(cur_width*scale), int(cur_height*scale)), Image.ANTIALIAS)

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img

    window['-IMAGE-'].update(data = bio.getvalue())

def pixels_to_metres():
    gs = mag * grain_size
    return f'{gs*1e3:.3g}mm' if gs >= 1e-3 else f'{gs*1e6:.3g}μm' if gs >= 1e-6 else f'{gs*1e9:.3g}nm'

#GUI layout
sg.theme('DarkBrown4')

lcol = [

    [sg.Frame('Stage', pad=(0,5), layout=[
        [sg.Slider((1, 5), default_value=1, orientation='horizontal', disable_number_display=True, key='-STAGE-',
            enable_events=True, size=(35.3, 20), pad=(10,5))],
        [sg.Text('Image{0}Threshold{0}Image Cleaning{0}Intercepts{0}Result'.format(" "*3))]])],

    [sg.Frame('Select Images', pad=(0,5), layout=[
        [sg.Text('Folder'), sg.In(size=(30,1), enable_events=True ,key='-FOLDER-'), sg.FolderBrowse()],
        [sg.Listbox(values=[r'Grainsizer App\Coloured Test.jpg', r'Grainsizer App\Grey Test.png'],
            enable_events=True, size=(44, 10), key='-FILE LIST-')]])],

    [sg.Frame('Magnification', pad=(0,5), layout=[
        [sg.Text('This is the measured in metres / pixel')],
        [sg.Button('Calculate', key='-CALC-'), sg.Input(default_text='Magnification', size=(12,1), enable_events=True, key='-MAG-', pad=((166,10), (0,0)))]])],

    [sg.Frame('Threshold', pad=(0,5), layout=[
        [sg.Text('The minimum colour gradient of the grain boundaries')],
        [sg.Slider((0.0, 0.5), default_value=0.25, resolution=0.001, orientation='horizontal', disable_number_display=True, size=(30,20), enable_events=True, key='-TSLIDER-'),
            sg.Input(default_text='0.25', size=(5,1), enable_events=True, pad=((10,10), (0,0)), key='-THRESH-')]])],

    [sg.Frame('Image Cleaning', pad=(0,5), layout=[
        [sg.Text('Maximum size in pixels of particles to be removed')],
        [sg.Slider((0, 800), default_value=400, resolution=5, orientation='horizontal', disable_number_display=True, size=(30,20), enable_events=True, key='-PSLIDER-'),
            sg.Input(default_text='400', size=(5,1), enable_events=True, pad=((10,10), (0,0)), key='-PARTICLES-')],
    
        [sg.Text('Approximate width in pixels of grain boundaries')],
        [sg.Slider((1, 5), default_value=1, resolution=1, orientation='horizontal', disable_number_display=True, size=(30,20), enable_events=True, key='-GBWSLIDER-'),
            sg.Input(default_text='1', size=(5,1), enable_events=True, pad=((10,10), (0,0)), key='-GBWIDTH-')]])],

    [sg.Frame('Intercepts', pad=(0,5), layout=[
        [sg.Text('Distance in pixels between red intercept lines')],
        [sg.Slider((10, 200), default_value=100, resolution=10, orientation='horizontal', disable_number_display=True, size=(30,20), enable_events=True, key='-SSLIDER-'),
            sg.Input(default_text='100', size=(5,1), enable_events=True, pad=((10,10), (0,0)), key='-SEP-')]])],

    [sg.Frame('Results', pad=(0,5), layout=[
        [sg.Column([[sg.Text('Average grainsize is not yet calculated'.ljust(100), key='-RES-')]], size=(340, 30), pad=(0,0))]])],
    
    [sg.Text('Made by Ayham Saffar. Check out my GitHub for more!', text_color='grey')]
]

img = sg.Image(r'Grainsizer App\New Logo.png', key='-IMAGE-')

layout = [[sg.Column(lcol, justification='left'), img]]

window = sg.Window('Grainsizer X', layout)

#GUI logic
while True:  # Event Loop

    event, values = window.read()
    print(event, values)

    if event == sg.WIN_CLOSED or event in ('Close', None):
        break

    if event == '-STAGE-':

        if 'filename' not in globals(): #if a file has not been selected
            sg.popup('Please select an image before beginning analysis', title='Error',
                auto_close=True, auto_close_duration=3)
            window['-STAGE-'].update(1)
            values['-STAGE-'] = 1

        else:
            if values['-STAGE-'] == 1:
                fig, iamge_height, image_length = open_fig()
                display_image(fig)
            
            if values['-STAGE-'] == 2:
                tfig, dfig = threshold_fig()
                display_image(dfig)

            if values['-STAGE-'] == 3:
                afig, dfig = artifact_fig()
                display_image(dfig)
    
            if values['-STAGE-'] >= 4:
                ifig, grain_size = intercept_fig()
                display_image(ifig)

                if values['-MAG-'] != 'Magnification':
                    window['-RES-'].update(f'Average grainsize is ' + pixels_to_metres())
                else:
                    window['-RES-'].update(f'Average grainsize is {int(grain_size)} pixels. (no magnification)')

    if event == '-FOLDER-': # A file was chosen from file explorer
        
        folder = values['-FOLDER-']
        
        try:
            file_list = os.listdir(folder)
            fnames = [f for f in file_list if os.path.isfile(
                os.path.join(folder, f)) and f.lower().endswith((".png", ".jpg", "jpeg", ".tiff", ".bmp"))]
            window['-FILE LIST-'].update(fnames)
        except:
            sg.popup('No files found in this folder', title='Error',
                auto_close=True, auto_close_duration=3)

    if event == '-FILE LIST-':    # A file was chosen from the listbox

        filename = os.path.join(values['-FOLDER-'], values['-FILE LIST-'][0])
        window['-STAGE-'].update(1)
        fig, image_height, image_length = open_fig()
        display_image(fig)

    if event == '-CALC-':

        if 'fig' not in globals(): #if a figure has not been loaded
            sg.popup('Please select an image before beginning finding magnification', title='Error',
                auto_close=True, auto_close_duration=3)
        
        else:
            try:
                sbcoords, mag = mag_window()
                window['-MAG-'].update(f'{mag:.4g}')

                #Colours scale bar borders red
                y1, y2, x1, x2 = sbcoords
                fig[y1, x1:x2+1] = [255, 0, 0]
                fig[y2, x1:x2+1] = [255, 0, 0]
                fig[y1:y2+1, x1] = [255, 0, 0]
                fig[y1:y2+1, x2] = [255, 0, 0]

                display_image(fig)
            
            except: #if the mag window is closed without any data being entered
                pass
    
    if event == '-MAG-':
        mag = float(values['-MAG-'])
        if values['-STAGE-'] >= 4:
            window['-RES-'].update(f'Average grainsize is ' + pixels_to_metres())

    if event == '-TSLIDER-' or event == '-THRESH-':

        if event == '-TSLIDER-':
            window['-THRESH-'].update(float(values['-TSLIDER-']))
            values['-THRESH-'] = float(values['-TSLIDER-'])

        if event == '-THRESH-':
            window['-TSLIDER-'].update(float(values['-THRESH-']))
            values['-TSLIDER-'] = float(values['-THRESH-'])

        if 'tfig' in globals(): #if a thresholded figure has been generated
            window['-STAGE-'].update(2)
            values['-STAGE-'] = 2
            tfig, dfig = threshold_fig()
            display_image(dfig)

    if event == '-PSLIDER-' or event == '-PARTICLES-':

        if event == '-PSLIDER-':
            window['-PARTICLES-'].update(int(values['-PSLIDER-']))
            values['-PARTICLES-'] = int(values['-PSLIDER-'])

        if event == '-PARTICLES-':
            window['-PSLIDER-'].update(int(values['-PARTICLES-']))
            values['-PSLIDER-'] = int(values['-PARTICLES-'])

        if 'afig' in globals(): #if an artifacted figure has been generated
            afig, dfig = artifact_fig()
            display_image(dfig)

    if event == '-GBWSLIDER-' or event == '-GBWIDTH-':

        if event == '-GBWSLIDER-':
            window['-GBWIDTH-'].update(int(values['-GBWSLIDER-']))
            values['-GBWIDTH-'] = int(values['-GBWSLIDER-'])

        if event == '-GBWIDTH-':
            window['-GBWSLIDER-'].update(int(values['-GBWIDTH-']))
            values['-GBWSLIDER-'] = int(values['-GBWIDTH-'])

        if 'afig' in globals(): #if an artifacted figure has been generated
            afig, dfig = artifact_fig()
            display_image(dfig)
    
    if event == '-SSLIDER-' or event == '-SEP-':

        if event == '-SSLIDER-':
            window['-SEP-'].update(int(values['-SSLIDER-']))
            values['-SEP-'] = int(values['-SSLIDER-'])

        if event == '-SEP-':
            window['-SSLIDER-'].update(int(values['-SEP-']))
            values['-SSLIDER-'] = int(values['-SEP-'])

        if 'ifig' in globals(): #if an intercept figure has been generated
            ifig, grain_size = intercept_fig()
            display_image(ifig)

            if values['-MAG-'] != 'Magnification':
                window['-RES-'].update(f'Average grainsize is ' + pixels_to_metres())
            else:
                window['-RES-'].update(f'Average grainsize is {int(grain_size)} pixels. (no magnification)')

window.close()