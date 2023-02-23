from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
from brother_ql.raster import BrotherQLRaster
import os
import sys
from datetime import datetime

LIB_PATH = os.path.dirname(os.path.abspath(__file__))
print(LIB_PATH)
DIR = LIB_PATH + '/ui/'
LABEL_OUT = './label.png'

# choose correct label size from tabele below
# https://brother-ql.net/readme.html
'''
Name      Printable px   Description
12         106           12mm endless
29         306           29mm endless
38         413           38mm endless
50         554           50mm endless
54         590           54mm endless
62         696           62mm endless
102       1164           102mm endless
17x54      165 x  566    17mm x 54mm die-cut
17x87      165 x  956    17mm x 87mm die-cut
23x23      202 x  202    23mm x 23mm die-cut
29x42      306 x  425    29mm x 42mm die-cut
29x90      306 x  991    29mm x 90mm die-cut
39x90      413 x  991    38mm x 90mm die-cut
39x48      425 x  495    39mm x 48mm die-cut
52x29      578 x  271    52mm x 29mm die-cut
62x29      696 x  271    62mm x 29mm die-cut
62x100     696 x 1109    62mm x 100mm die-cut
102x51    1164 x  526    102mm x 51mm die-cut
102x152   1164 x 1660    102mm x 153mm die-cut
d12         94 x   94    12mm round die-cut
d24        236 x  236    24mm round die-cut
d58        618 x  618    58mm round die-cut
'''

def print_label(serial_number, test_result, date_time):
        ''' 
        Print label on Brother QL-700 series printer 
        with provided data: serial number, test result, and date time
        '''
        # im = Image.open('QRcode.png')
        # # im.resize((696, 696)) 
        width = 440
        height = 106
        size = 50
        top = 5
        x_pad = 5
        current_str = "S/N: " + serial_number
        pass_icon = chr(79)
        fail_icon = chr(88)

        image = Image.new(mode="1", size=(width, height), color=1)
        rubik_regular = ImageFont.truetype(DIR + 'rubik/Rubik-Light.ttf', size=44)
        draw = ImageDraw.Draw(image)
        draw.text(xy = (x_pad, top), text = current_str, align='left',
                font=rubik_regular, fill=0)

        rubik_regular = ImageFont.truetype(DIR + 'rubik/Rubik-Light.ttf', size=30)
        draw.text(xy = (x_pad, 70), text = date_time, align='left',
                font=rubik_regular, fill=0)

        if test_result:
                icon = pass_icon
        else:
                icon = fail_icon

        font_icon = ImageFont.truetype(DIR + 'heydings/heydings_icons.ttf', size=30)
        draw.text(xy = (380, 70), text = icon, align='right',
                font=font_icon, fill=0)

        image.save(LABEL_OUT)

        backend = 'pyusb'    # 'pyusb', 'linux_kernal', 'network'
        model = 'QL-700' # your printer model.
        #printer = 'usb://0x04f9:0x209b'    # Get these values from the Windows usb driver filter.  Linux/Raspberry Pi uses '/dev/usb/lp0'.
        printer = 'usb://0x04f9:0x2042' #can beobtained using command > brother_ql -b pyusb discover

        qlr = BrotherQLRaster(model)
        qlr.exception_on_warning = True

        instructions = convert(

                qlr=qlr, 
                images=[image],    #  Takes a list of file names or PIL objects.
                #label='29x90',
                label='12', 
                rotate='90',    # 'Auto', '0', '90', '270'
                threshold=70.0,    # Black and white threshold in percent.
                dither=False, 
                compress=False, 
                red=False,    # Only True if using Red/Black 62 mm label tape.
                dpi_600=False, 
                hq=True,    # False for low quality.
                cut=True

        )
        try:
                send(instructions=instructions, printer_identifier=printer, backend_identifier=backend, blocking=True)
                return True
        except ValueError as e:
                print("The lable printer is off. Please turn it on and try again.")
                return False


def main():
        serial_number = "K8HN5Y6BGN"
        test_result = True
        now = datetime.now()
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        s = print_label(serial_number, test_result, date_time)
        print(s)



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
