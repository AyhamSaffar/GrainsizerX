#GUI back end
import PySimpleGUI as sg
import os.path
import io
import numpy as np
from PIL import Image
from skimage import io as skio
from skimage.morphology import remove_small_objects, skeletonize, closing, disk
from skimage.filters import sobel
from skimage.color import rgb2gray, gray2rgb

def dot(fig, y, x, rad):
    '''
    Creates a blue dot
    '''
    fig[y-(rad//2) : y+(rad//2)+1, x-(rad//2) : x+(rad//2)+1] = [0, 0, 255]

def open_fig():
    '''
    Opens and formats the currently selected file into a resized array (fig)
    '''
    fig = skio.imread(filename)
    fig_height, fig_width = np.shape(fig)[:2]

    if 'sbcoords' in globals(): del globals()['sbcoords']
    if 'cfig' in globals(): del globals()['cfig']
    
    if len(np.shape(fig)) == 2: #if image is in greyscale
        fig = gray2rgb(fig)
    
    if np.shape(fig)[2] == 4: #if image has a transparency layer
        fig = fig[:,:,:3]

    fig = np.array(fig, dtype=np.uint8)

    #defining intensity gradient image for use in threshold stage here (done to reduce unnecessary calls)
    global igfig
    igfig = sobel(rgb2gray(fig))

    #resize image window
    target_width, target_height = 1460, 990
    scale = min(target_height/fig_height, target_width/fig_width)
    new_image_size = (int(fig_width*scale), int(fig_height*scale))
    window['-IMAGE-'].set_size(new_image_size)
    window['-IMAGE-'].change_coordinates((0,fig_height), (fig_width, 0))

    return fig, fig_height, fig_width, new_image_size

def get_scalebar_coords():
    '''
    Allows the user to draw a box around the scale bar on the image and returns the coordinates of
    the corners of the box. This allows this area to be ignored during analysis
    '''
    window['-SCALEBAR-'].update(button_color=my_red)

    while True:
        event, values = window.read()
        #print(event, values)
        x, y = values["-IMAGE-"]

        if event == '-IMAGE-':  # if there's a "IMAGE" event, then it's a mouse click
            start_point = (x, y)
            
        if event == '-IMAGE-+MOTION' and 'start_point' in locals():
            if 'prev_rect' in locals():
                window['-IMAGE-'].delete_figure(prev_rect)

            end_point = (x, y)
            prev_rect = window['-IMAGE-'].draw_rectangle(start_point, end_point, line_color='blue')

        if event == '-IMAGE-+UP':  # The left mouse button has been let go
            #saving scalebar coords as y1, y2, x1, x2
            sbcoords = [min(start_point[1], end_point[1]), max(start_point[1], end_point[1]),
                min(start_point[0], end_point[0]), max(start_point[0], end_point[0])]
            window['-IMAGE-'].delete_figure(prev_rect)
            window['-SCALEBAR-'].update(button_color=my_grey)
            break
    
    return sbcoords

def get_scaleline_pixel_len():
    '''
    Allows the user to highlight the scalebar and returns its length in pixels
    '''
    window['-SCALELINE-'].update(button_color=my_red)

    while True:
        event, values = window.read()
        #print(event, values)
        x, y = values["-IMAGE-"]

        if event == "-IMAGE-":  # if the right mouse button is being pushed down
            start_point = (x, y)

        if event == '-IMAGE-+MOTION' and 'start_point' in locals():
            if 'prev_line' in locals():
                window['-IMAGE-'].delete_figure(prev_line)
            
            end_point = (x, start_point[1])
            prev_line = window['-IMAGE-'].draw_line(start_point, end_point, color='red', width=3)

        if event == '-IMAGE-+UP':  # if the right mouse button has been let go
            slplen = max(start_point[0], end_point[0]) - min(start_point[0], end_point[0])
            window['-IMAGE-'].delete_figure(prev_line)
            window['-SCALELINE-'].update(button_color=my_grey)
            break

    return slplen

def threshold_fig():
    '''
    Thresholds the figure to find where the grain bounderies are (tfig)
    and creates a new figure highlighting the grain bounderies in red (dfig)
    '''
    tfig = igfig > float(values['-THRESH-'])
    #igfig = sobel(rgb2gray(fig)) as ran in open_fig stage

    if 'sbcoords' in globals():
        y1, y2, x1, x2 = sbcoords
        tfig[y1:y2+1, x1:x2+1] = 0
    
    dfig = np.array(fig)
    dfig[tfig==1] = [255, 0, 0]

    return tfig, dfig

def artifact_fig():
    '''
    Removes small particles from the thresholded figures and skelotonizes
    the grain boundaries (afig). Creates a new figure (dfig) showing the 
    thresholded figure in white and the artifact free figure in red
    '''
    afig = remove_small_objects(tfig, min_size=int(values['-PARTICLES-']))
    shape = disk(int(values['-GBWIDTH-']) + 2) #grain boundary width
    afig = closing(afig, shape)
    afig = skeletonize(afig)

    dfig = np.zeros([fig_height, fig_width, 3], dtype=np.uint8)
    if values['-VIEW-'] == 2: #if change view selected
        dfig[tfig==1] = [255, 0, 0]
        dfig[afig==1] = [255, 255, 255]
    else: #if chage view selected
        dfig[:] = fig
        dfig[afig==1] = [255, 0 ,0]
    
    return afig, dfig

def correct_fig(drawing=False, clear=False):
    '''
    Allows the user to draw on new grain boundaries or rub out old ones.
    Returns a figure with these changes made.
    '''
    global event
    global csize
    global values

    if 'cfig' in globals():
        global cfig
    else:
        cfig = np.array(afig)

    if clear:
        cfig = np.array(afig)

    if drawing:
        _fig = np.zeros([fig_height, fig_width], dtype=np.uint8) # temp fig

        while event != '-IMAGE-+UP':
            event, values = window.read()
            #print(event, values)
            
            x, y = values["-IMAGE-"]

            if correcting == 'ADD':
                window['-IMAGE-'].draw_point(point=(x, y), size=8, color='blue')
                _fig[(y-csize if y-csize >= 0 else 0) : y+csize+1, (x-csize if x-csize >= 0 else 0) : x+csize+1] = 1

            if correcting == 'REMOVE':
                window['-IMAGE-'].draw_rectangle(top_left=(x-csize, y-csize), bottom_right=(x+csize, y+csize), fill_color='red', line_width=0)
                cfig[(y-csize if y-csize >= 0 else 0) : y+csize+1, (x-csize if x-csize >= 0 else 0) : x+csize+1] = 0

        window['-IMAGE-'].erase()
        _fig = skeletonize(_fig)
        cfig[_fig==1] = 1
        if 'sbcoords' in globals():
            y1, y2, x1, x2 = sbcoords
            cfig[y1:y2+1, x1:x2+1] = 0


    dfig = np.zeros([fig_height, fig_width, 3], dtype=np.uint8)

    if values['-VIEW-'] == 2: #if change view selected
        dfig[afig==1] = [255, 255, 255] # old array is white
        dfig[cfig==1] = [255, 0, 0] # new array is red
        dfig[(cfig==1) & (afig==0)] = [0, 0, 255] # new array but not old array is blue
    
    else: #if image view selected
        dfig[:] = fig
        dfig[cfig==1] = [255, 0, 0] # new array is red
    
    return cfig, dfig 
    
def intercept_fig():
    '''
    Creates vertical and horizontal lines at regular intervals and
    counts the number of times a grain boundary intercepts one of these lines.
    This is used to work out the average grain size and a new figure showing
    these intercepts (dfig) is created
    '''
    sep = int(values['-SEP-'])
    rx, ry = range(0, fig_width, sep)[1:], range(0, fig_height, sep)[1:]
    counter = 0

    if values['-VIEW-'] == 2: #if change view selected
        ifig = gray2rgb(cfig)
        ifig = np.array(ifig*255, dtype=np.uint8)

    else: #if image view selected
        ifig = np.array(fig)

    ifig[ry,:] = [255, 0, 0] 
    ifig[:, rx] = [255, 0, 0] 
    
    #counting and marking intercepts
    counter += len([dot(ifig, j, i, 5) for j in ry for i in range(fig_width)
        if [cfig[j][i-1], cfig[j][i]]  == [0, 1]])

    counter += len([dot(ifig, j, i, 5) for i in rx for j in range(fig_height)
        if [cfig[j-1][i], cfig[j][i]]  == [0, 1]])
    
    line_len = fig_height*len(rx) + fig_width*len(ry)
    
    if 'sbcoords' in globals(): #if scalebar has been selected
        y1, y2, x1, x2 = sbcoords
        line_len -= (x2-x1) * len([i for i in ry if y1 <= i <= y2])
        line_len -= (y2-y1) * len([i for i in rx if x1 <= i <= x2])

        if values['-VIEW-'] == 2:
            ifig[y1:y2+1, x1:x2+1] = 255 * gray2rgb(cfig[y1:y2+1, x1:x2+1])
    
        elif values['-VIEW-'] == 1:
            ifig[y1:y2+1, x1:x2+1] = np.array(fig[y1:y2+1, x1:x2+1])

    pixel_grain_size = line_len / counter 

    return ifig, pixel_grain_size

def display_image(fig):
    '''
    Adds scale bar border to figure and converts figure array into 
    resized PIL object so that it can be displayed in the GUI window
    '''
    if 'sbcoords' in globals():
        temp = np.array(fig)
        y1, y2, x1, x2 = sbcoords
        temp[y1, x1:x2+1] = [0, 0, 255]
        temp[y2, x1:x2+1] = [0, 0, 255]
        temp[y1:y2+1, x1] = [0, 0, 255]
        temp[y1:y2+1, x2] = [0, 0, 255]
        img = Image.fromarray(temp)
        del temp
    else:
        img = Image.fromarray(fig)

    img = img.resize(new_image_size, Image.ANTIALIAS)

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    window['-IMAGE-'].draw_image(data = bio.getvalue(), location=(0,0))

def display_grain_size():
    '''
    Displays either the true grain size if the magnification has been entered or
    the pixel grain size if not
    '''
    if 'mag' not in globals():
        window['-RES-'].update(f'Average grainsize is {int(pixel_grain_size)} pixels. (no magnification)')
    else:
        tgsm = mag * pixel_grain_size  #true grain size in metres
        true_grain_size = f'{tgsm*1e3:.3g}mm' if tgsm >= 1e-3 else f'{tgsm*1e6:.3g}μm' \
            if tgsm >= 1e-6 else f'{tgsm*1e9:.3g}nm'
        window['-RES-'].update(f'Average grainsize is ' +  true_grain_size)

class Slider(sg.Slider):
    '''
    Adding the ability to adjust the value of slider elements with the scroll wheel
    NOTE window[<SLIDER KEY STRING>].initial(window) must be called for each slider
    '''

    def initial(self, window):
        self.Widget.bind('<MouseWheel>', lambda event, window=window:self.callback(event, window))

    def callback(self, event, window):
        value = float(self.Widget.get())
        if event.num == 5 or event.delta < 0:
            self.update(value - self.Resolution)
        elif event.num == 4 or event.delta > 0:
            self.update(value + self.Resolution)
        if self.ChangeSubmits:
            window.write_event_value(self.Key, float(self.Widget.get()))
    
sg.theme('DarkBrown4')

lcol = [
    [sg.Frame('Stage', pad=(0,5), element_justification='center', layout=[
        [Slider((1, 5), default_value=1, orientation='horizontal', disable_number_display=True, key='-STAGE-',
            enable_events=True, size=(35.3, 20), pad=(10,5))],
        [sg.Text('Image{0}Threshold{0}Cleaning{0}Correcting{0}Intercepts'.format(" "*4))],
        
        [sg.Text('Image View'), Slider((1,2), default_value=1, resolution=1, orientation='horizontal',
            disable_number_display=True, enable_events=True, key='-VIEW-', size=(7, 20)), sg.Text('Change View')]])],

    [sg.Frame('Select Images', pad=(0,5), layout=[
        [sg.Text('Folder'), sg.In(size=(30,1), enable_events=True ,key='-FOLDER-'), sg.FolderBrowse()],
        [sg.Listbox(values=[r'Grainsizer App\Coloured Test.jpg', r'Grainsizer App\Grey Test.png'],
            enable_events=True, size=(44, 10), key='-FILE LIST-')]])],

    [sg.Frame('Magnification', pad=(0,5), layout=[
        [sg.Text('The scalebar area that will be ignored in analysis'), sg.Sizer(42, 0)],
        [sg.Button('Draw', key='-SCALEBAR-'), sg.Button('Clear', key='-SBCLEAR-')],

        [sg.Text('The true and image length of the scale line')],
        [sg.Input('', key='-SLTLEN-', size=(10, 1), enable_events=True),
            sg.Combo(['mm', 'μm', 'nm'], key='-SLTUNIT-', size=(5, 1), enable_events=True),
            sg.Button('Draw', key='-SCALELINE-')],
        
        [sg.Text('Final Magnification in metres / pixel:'), sg.Input(default_text='',
            size=(14,1), enable_events=True, key='-MAG-')]])],

    [sg.Frame('Threshold', pad=(0,5), layout=[
        [sg.Text('The minimum colour gradient of the grain boundaries')],
        [Slider((0.0, 0.5), default_value=0.25, resolution=0.005, orientation='horizontal', disable_number_display=True, size=(30,20), enable_events=True, key='-TSLIDER-'),
            sg.Input(default_text='0.25', size=(5,1), enable_events=True, pad=((10,10), (0,0)), key='-THRESH-')]])],

    [sg.Frame('Cleaning', pad=(0,5), layout=[
        [sg.Text('Maximum size in pixels of particles to be removed')],
        [Slider((0, 800), default_value=400, resolution=5, orientation='horizontal', disable_number_display=True, size=(30,20), enable_events=True, key='-PSLIDER-'),
            sg.Input(default_text='400', size=(5,1), enable_events=True, pad=((10,10), (0,0)), key='-PARTICLES-')],
    
        [sg.Text('Approximate width in pixels of grain boundaries')],
        [Slider((1, 10), default_value=1, resolution=1, orientation='horizontal', disable_number_display=True, size=(30,20), enable_events=True, key='-GBWSLIDER-'),
            sg.Input(default_text='1', size=(5,1), enable_events=True, pad=((10,10), (0,0)), key='-GBWIDTH-')]])],

    [sg.Frame('Correcting', pad=(0,5), layout=[
        [sg.Column([[sg.Text('Draw on and rub out boundaries as needed')]], size=(340, 30), pad=(0,0))],
        [sg.Button('Add', key='-ADD-'), sg.Button('Remove', key='-REMOVE-'), sg.Button('Clear', key='-CCLEAR-')]])],

    [sg.Frame('Intercepts', pad=(0,5), layout=[
        [sg.Text('Distance in pixels between red intercept lines')],
        [Slider((10, 200), default_value=100, resolution=10, orientation='horizontal', disable_number_display=True, size=(30,20), enable_events=True, key='-SSLIDER-'),
            sg.Input(default_text='100', size=(5,1), enable_events=True, pad=((10,10), (0,0)), key='-SEP-')]])],

    [sg.Frame('Results', pad=(0,5), layout=[
        [sg.Column([[sg.Text('Average grainsize is not yet calculated'.ljust(100), key='-RES-')]], size=(340, 30), pad=(0,0))]])],
    
    [sg.Text('Check out my GitHub at /AyhamSaffar for more!', text_color='grey', enable_events=True)]
]

img = sg.Graph(canvas_size=((1460, 990)), graph_bottom_left=(0, 0), graph_top_right=(10, 10),
            key="-IMAGE-", enable_events=True, background_color='white', drag_submits=True)

window = sg.Window(title='Grainsizer X', layout=[[sg.Column(lcol, justification='left'), img]],
            finalize=True, return_keyboard_events=True, icon=r'Grainsizer App\Icon.ico')

#initializing new slider class that allows scroll wheel adjusting for each slider
window['-STAGE-'].initial(window)
window['-VIEW-'].initial(window)
window['-TSLIDER-'].initial(window)
window['-PSLIDER-'].initial(window)
window['-GBWSLIDER-'].initial(window)
window['-SSLIDER-'].initial(window)

#binding left click to toggle view
window.bind('<Button-3>', '-RCLICK-')

#binding cursor hovering over image to event
window['-IMAGE-'].bind('<Motion>', '+MOTION')

#custom colours
my_grey = '#252525'
my_red = '#af0404'

#adding logo to display
filename = r'Grainsizer App\Final Logo.jpg'
fig, fig_height, fig_width, new_image_size = open_fig()
display_image(fig)

#GUI logic
while True:  # Event Loop

    event, values = window.read()
    #print(event, values)

    if event == sg.WIN_CLOSED or event in ('Close', None):
        break

    if event in ['-STAGE-', '-VIEW-', '-RCLICK-']:

        if event == '-RCLICK-':
            window['-VIEW-'].update(2 if values['-VIEW-'] == 1 else 1)
            values['-VIEW-'] = 2 if values['-VIEW-'] == 1 else 1

        if values['-STAGE-'] == 1:
            fig, iamge_height, fig_width, new_image_size = open_fig()
            display_image(fig)
        
        elif values['-STAGE-'] == 2:
            tfig, dfig = threshold_fig()
            display_image(dfig)

        elif values['-STAGE-'] == 3:
            afig, dfig = artifact_fig()
            display_image(dfig)

        elif values['-STAGE-'] == 4:
            cfig, dfig = correct_fig(drawing=False)
            display_image(dfig)

        elif values['-STAGE-'] == 5:
            ifig, pixel_grain_size = intercept_fig()
            display_image(ifig)
            display_grain_size()

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
        if values['-FILE LIST-'][0].startswith('https'): #if filename is a URL
            filename = values['-FILE LIST-'][0]

        else: #if file is an actual file
            filename = os.path.join(values['-FOLDER-'], values['-FILE LIST-'][0])

        window['-STAGE-'].update(1)
        fig, fig_height, fig_width, new_image_size = open_fig()
        display_image(fig)
        
    if event == '-SCALEBAR-': 
        window['-IMAGE-'].set_cursor('arrow')
        if 'fig' in globals():
            window['-STAGE-'].update(1)
            if 'sbcoords' in globals(): del globals()['sbcoords']
            display_image(fig)
            sbcoords = get_scalebar_coords()
            display_image(fig)
        else:
            sg.popup('Please select an image first', title='Error',
                auto_close=True, auto_close_duration=3)

    if event == '-SBCLEAR-':
        if 'sbcoords' in globals():
            del globals()['sbcoords']
            window['-STAGE-'].update(1)
            display_image(fig)  

    if event in ['-SCALELINE-', '-SLTLEN-', '-SLTUNIT-']:

        if event == '-SCALELINE-':
            window['-IMAGE-'].set_cursor('arrow')
            scalelinepixellength = get_scaleline_pixel_len()

        if 'scalelinepixellength' in globals() and values['-SLTLEN-'] != '' and values['-SLTUNIT-'] != '':
            scalelinemetrelength = int(values['-SLTLEN-']) / (1e3 if values['-SLTUNIT-'] == 'mm' else 1e6 if values['-SLTUNIT-'] == 'μm' else 1e9)
            mag = scalelinemetrelength / scalelinepixellength
            window['-MAG-'].update(f'{mag:.5g}')
            
            if values['-STAGE-'] == 5:
                display_grain_size()

    if event == '-MAG-':
        try:
            mag = float(values['-MAG-'])
            if values['-STAGE-'] == 5:
                display_grain_size()
        except:
            window['-MAG-'].update(values['-MAG-'][:-1])
            sg.popup('Magnification must be a valid number', title='Error',
                auto_close=True, auto_close_duration=3)

    if event == '-TSLIDER-' or event == '-THRESH-':
        if 'cfig' in globals(): del cfig

        if event == '-TSLIDER-':
            window['-THRESH-'].update(float(values['-TSLIDER-']))
            values['-THRESH-'] = float(values['-TSLIDER-'])

        if event == '-THRESH-':
            window['-TSLIDER-'].update(float(values['-THRESH-']))
            values['-TSLIDER-'] = float(values['-THRESH-'])

        if 'filename' in globals(): #if a image has been selected
            window['-STAGE-'].update(2)
            values['-STAGE-'] = 2
            tfig, dfig = threshold_fig()
            display_image(dfig)

    if event == '-PSLIDER-' or event == '-PARTICLES-':
        if 'cfig' in globals(): del cfig

        if event == '-PSLIDER-':
            window['-PARTICLES-'].update(int(values['-PSLIDER-']))
            values['-PARTICLES-'] = int(values['-PSLIDER-'])

        if event == '-PARTICLES-':
            window['-PSLIDER-'].update(int(values['-PARTICLES-']))
            values['-PSLIDER-'] = int(values['-PARTICLES-'])

        if 'tfig' in globals(): #if an thresholded figure has been generated
            window['-STAGE-'].update(3)
            values['-STAGE-'] = 3
            afig, dfig = artifact_fig()
            display_image(dfig)

    if event == '-GBWSLIDER-' or event == '-GBWIDTH-':
        if 'cfig' in globals(): del cfig

        if event == '-GBWSLIDER-':
            window['-GBWIDTH-'].update(int(values['-GBWSLIDER-']))
            values['-GBWIDTH-'] = int(values['-GBWSLIDER-'])

        if event == '-GBWIDTH-':
            window['-GBWSLIDER-'].update(int(values['-GBWIDTH-']))
            values['-GBWSLIDER-'] = int(values['-GBWIDTH-'])

        if 'tfig' in globals(): #if an thresholded figure has been generated
            window['-STAGE-'].update(3)
            values['-STAGE-'] = 3
            afig, dfig = artifact_fig()
            display_image(dfig)
    
    if event in ['-ADD-', '-REMOVE-', '-CCLEAR-'] and values['-STAGE-'] in [3, 4, 5]: 
        window['-IMAGE-'].set_cursor('None')
        
        if values['-STAGE-'] in [3, 5]:
            window['-STAGE-'].update(4)
            values['-STAGE-'] = 4
            cfig, dfig = correct_fig()
            display_image(dfig)

        if event == '-ADD-':
            window['-REMOVE-'].update(button_color=my_grey)
            window['-ADD-'].update(button_color=my_red)
            csize = 4
            correcting = 'ADD'
    
        if event == '-REMOVE-':
            window['-ADD-'].update(button_color=my_grey)
            window['-REMOVE-'].update(button_color=my_red)
            csize = 4
            correcting = 'REMOVE'
        
        if event == '-CCLEAR-':
            cfig, dfig = correct_fig(clear=True)
            display_image(dfig)

    if event in ['-IMAGE-+MOTION', 'MouseWheel:Up', 'MouseWheel:Down'] and 'correcting' in globals():
        if 'prev_shape' in globals():
            window['-IMAGE-'].delete_figure(prev_shape)

        if event == 'MouseWheel:Up':
            csize += 1

        if event == 'MouseWheel:Down':
            csize = csize-1 if csize>4 else 4

        x, y = values['-IMAGE-']
        
        if correcting == 'ADD':
            prev_shape = window['-IMAGE-'].draw_circle(center_location=(x, y), radius=4, line_color='blue')
        
        if correcting == 'REMOVE':
            prev_shape = window['-IMAGE-'].draw_rectangle(top_left=(x-csize, y-csize), bottom_right=(x+csize, y+csize), line_color='red')

    if event == "-IMAGE-" and 'correcting' in globals():
        cfig, dfig = correct_fig(drawing=True)
        display_image(dfig)

    if values['-STAGE-'] != 4 and 'correcting' in globals():
        del correcting
        window['-IMAGE-'].set_cursor('arrow')
        window['-ADD-'].update(button_color=my_grey)
        window['-REMOVE-'].update(button_color=my_grey)

    if event == '-SSLIDER-' or event == '-SEP-':
        if event == '-SSLIDER-':
            window['-SEP-'].update(int(values['-SSLIDER-']))
            values['-SEP-'] = int(values['-SSLIDER-'])

        if event == '-SEP-':
            window['-SSLIDER-'].update(int(values['-SEP-']))
            values['-SSLIDER-'] = int(values['-SEP-'])

        if 'cfig' in globals(): #if a cleaned figure has been generated
            window['-STAGE-'].update(5)
            values['-STAGE-'] = 5
            ifig, pixel_grain_size = intercept_fig()
            display_image(ifig)
            display_grain_size()

window.close()
