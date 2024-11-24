from pdfwatermark.src.pdf_watermark.handler import add_watermark_to_pdf
from pdfwatermark.src.pdf_watermark.options import InsertOptions, DrawingOptions

import argparse
import barcode
from barcode.writer import SVGWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, inch
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
import tkinter as tk
from tkinter import filedialog
import os
from svglib.svglib import svg2rlg
from reportlab.graphics import renderSVG
from PyPDF2 import PdfReader, PdfWriter
import io
import fitz  # PyMuPDF for PDF handling
from pypdf import PdfReader
from test import add_first_page_to_pdf
import numpy as np

# Function to generate barcode as an SVG
def generate_barcode_svg(text, filename):
    code128 = barcode.get('code128', text, writer=SVGWriter())
    barcode_svg_path = filename
    code128.save(barcode_svg_path, options={'font_size': 6, "text_distance": 4})  # Save as SVG
    return barcode_svg_path + ".svg"

# Function to scale SVG and save it
def scale_svg(svg_path, scale_factor):
    scale_factor_x, scale_factor_y = scale_factor
    drawing = svg2rlg(svg_path)
    drawing.width *= scale_factor_x
    drawing.height *= scale_factor_y
    drawing.scale(scale_factor_x, scale_factor_y)
    scaled_svg_path = svg_path.replace(".svg", "_scaled.svg")
    renderSVG.drawToFile(drawing, scaled_svg_path)
    return scaled_svg_path

# Function to get dimensions of the SVG barcode
def get_barcode_dimensions(svg_path):
    drawing = svg2rlg(svg_path)
    return drawing.width, drawing.height

def draw_barcode(barcode_svg_path, template_pdf_path, output_pdf_path, row, col):
    # Calculate coordinates for InsertOptions
    offsetx, offsety = 200+75, 142
    # page_height, page_width = letter  # Page dimensions for adjustment
    page_width, page_height = PdfReader(template_pdf_path).pages[0].mediabox[-2:]
    # Get dimensions of the generated barcode
    barcode_width, barcode_height = get_barcode_dimensions(barcode_svg_path)

    # Select bounding box interactively
    bounding_box = (166, 43, 262, 95)  # Replace with select_bounding_box(template_pdf_path) if needed
    x1, y1, x2, y2 = bounding_box
    # print(bounding_box)

    bbox_width = x2 - x1
    bbox_height = y2 - y1

    # if offset != 0:
    #     x1 = x1 + offset * page_height + bbox_width
    #     x2 = x2 + offset * page_height + bbox_width

    # Compute scale factor based on the bounding box size
    scale_x = bbox_width / barcode_width
    scale_y = bbox_height / barcode_height
    # scale = min(scale_x, scale_y)  # Use the smaller scale to maintain aspect ratio

    # Scale the SVG and save it
    scaled_barcode_svg_path = scale_svg(barcode_svg_path, [scale_x, scale_y])

    # for k in range(8):
        # row, col = k //2, k % 2
    opts_in = InsertOptions(
        x=((176 + offsetx * col + (row > 0)*40)/page_width),
        y=(page_height-(44 + offsety * row + max((1 * (row > 1) * (col)), 0) + max((56 * (row-1)), 0) + max((23 * (col))*(row > 0), 0))) / page_height,
        horizontal_alignment="center",
        svg=scaled_barcode_svg_path,
    )
    # opts_in = InsertOptions(
    #     x=0.1,
    #     y=0.5,
    #     horizontal_alignment="center",
    #     svg=scaled_barcode_svg_path,
    # )
    # Drawing options for watermark placement
    opts = DrawingOptions(
        watermark="1.png",
        opacity=1,
        angle=0,  # Angle set to 0 for upright barcode
        text_color="#000000",
        text_font="Helvetica",
        text_size=12,
        unselectable=False,
        image_scale=[1.1, 0.9],  # Adjust scale as needed
        save_as_image=False,
        dpi=300,
    )

    # Apply the barcode as a watermark to the PDF
    add_watermark_to_pdf(template_pdf_path, output_pdf_path, opts, opts_in)
    pass
    # opts_in = InsertOptions(y=(1-(bbox_height/page_height)), x=opts_in.x,horizontal_alignment="center", svg=barcode_svg_path)
    # scaled_barcode_svg_path = scale_svg(scaled_barcode_svg_path, [1.1, 1.1])

    # opts_in_ = InsertOptions(y=opts_in.y+0.1, x=opts_in.x + 0.690,horizontal_alignment="center", svg=scaled_barcode_svg_path)
    # opts_ = DrawingOptions(
    #     watermark="1.png",
    #     opacity=1,
    #     angle=90,  # Angle set to 0 for upright barcode
    #     text_color="#000000",
    #     text_font="Helvetica",
    #     text_size=12,
    #     unselectable=False,
    #     image_scale=[1, 1],  # Adjust scale as needed
    #     save_as_image=False,
    #     dpi=300,
    # )
    # add_watermark_to_pdf(output_pdf_path, output_pdf_path, opts_, opts_in_)
    return output_pdf_path
# Function to interactively draw a bounding box on a PDF page
def select_bounding_box(pdf_path):
    # Load the PDF page using PyMuPDF (fitz)
    pdf_document = fitz.open(pdf_path)
    page = pdf_document.load_page(0)  # Load the first page
    pix = page.get_pixmap()
    img_path = "page_image.png"
    pix.save(img_path)

    # Create a Tkinter window to display the PDF image
    root = tk.Tk()
    root.title("Select Bounding Box")

    canvas_widget = tk.Canvas(root, width=pix.width, height=pix.height)
    canvas_widget.pack()

    pdf_image = tk.PhotoImage(file=img_path)
    canvas_widget.create_image(0, 0, anchor=tk.NW, image=pdf_image)

    rect = None
    start_x = start_y = 0

    def on_mouse_down(event):
        nonlocal start_x, start_y
        start_x, start_y = event.x, event.y

    def on_mouse_up(event):
        nonlocal rect
        end_x, end_y = event.x, event.y
        rect = (start_x, start_y, end_x, end_y)
        canvas_widget.create_rectangle(start_x, start_y, end_x, end_y, outline="red")

    def submit_bounding_box():
        nonlocal rect
        if rect:
            root.destroy()
        else:
            print("No bounding box selected.")

    canvas_widget.bind("<ButtonPress-1>", on_mouse_down)
    canvas_widget.bind("<ButtonRelease-1>", on_mouse_up)

    submit_button = tk.Button(root, text="Submit", command=submit_bounding_box)
    submit_button.pack()

    root.mainloop()
    pdf_document.close()

    if rect:
        print(f"Selected bounding box: {rect}")  # Debug output
        return rect
    else:
        raise ValueError("Bounding box not selected")
    
def add_text_to_pdf(template_pdf_path, output_pdf_path, row, col, montant='', annee='', gare=''):
    # Open the template PDF
    pdf_document = fitz.open(template_pdf_path)
    page = pdf_document.load_page(0)
    offset = 400+20
    offsetx, offsety = 200+95, 198
    # Iterate over each page
    for idx in range(1):
        
        # Set text properties
        text_font = "helvetica-bold"
        text_size = 9
        text_color = (0, 0, 0)  # Black color in RGB

        # Add text to specific positions
        # page.insert_text((100, 700), f"Montant: {montant}", fontname=text_font, fontsize=text_size, color=text_color, rotate=90)
        page.insert_text((54+row * (offsetx-50), 89 + col * offsety), f"{gare}", fontname=text_font, fontsize=text_size, color=text_color, rotate=0)
        page.insert_text((195+row * (offsetx+35), 89 + col * offsety), f"{annee}", fontname=text_font, fontsize=text_size, color=text_color, rotate=0)
        page.insert_text((140+row * (offsetx+20), 89 + col * offsety), f"{montant}", fontname=text_font, fontsize=text_size, color=text_color, rotate=0)

        # page.insert_text((53, 763-(offset*idx)), f"{gare}", fontname=text_font, fontsize=text_size, color=text_color, rotate=0)
        # page.insert_text((53, 50), f"{annee}", fontname=text_font, fontsize=text_size, color=text_color, rotate=0)
        # page.insert_text((69, 745-(offset*idx)), f"{montant}", fontname=text_font, fontsize=text_size, color=text_color, rotate=0)

        # page.insert_text((53+125, 763-(offset*idx)), f"{gare}", fontname=text_font, fontsize=text_size, color=text_color, rotate=0)
        # page.insert_text((53+125+1, 700-(offset*idx)), f"{annee}", fontname=text_font, fontsize=text_size, color=text_color, rotate=0)

        # page.insert_text((70+233, 770-100-(offset*idx)), f"{montant}", fontname=text_font, fontsize=text_size+8, color=text_color, rotate=0)

    # Save the modified PDF to the output path
    pdf_document.save(output_pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    pdf_document.close()

    return output_pdf_path
# Main logic to generate barcode and place it using the selected bounding box
if __name__ == "__main__":
    from tqdm import tqdm
    parser = argparse.ArgumentParser(description="Generate a barcode and place it on a PDF.")
    parser.add_argument("--pdftemplate", required=True, help="Path to save the output PDF with the barcode")
    parser.add_argument("--gare", required=True, help="Path to save the output PDF with the barcode")
    parser.add_argument("--annee", required=True, help="Path to save the output PDF with the barcode")
    parser.add_argument("--montant", type=int, required=True, help="Path to save the output PDF with the barcode")
    parser.add_argument("--barcodeprefix", required=True, help="Text to encode in the barcode")
    parser.add_argument("--output", default='res.pdf', help="Path to save the output PDF with the barcode")
    parser.add_argument("--min", type=int, default=1, help="Path to save the output PDF with the barcode")
    parser.add_argument("--max", type=int, default=50, help="Path to save the output PDF with the barcode")
    parser.add_argument("--ncarnet", type=int, default=50, help="Path to save the output PDF with the barcode")

    args = parser.parse_args()

    text_to_encode = args.barcodeprefix
    barcode_filename = "barcode_image"
    output_pdf_path = args.output

    # Open file dialog to choose a template PDF
    template_pdf_path = args.pdftemplate
    if not template_pdf_path:
        print("No PDF selected. Exiting.")
        exit()
    outdir = os.path.join("output", "tickets", "{}-{}{}".format(args.gare, args.barcodeprefix, os.path.sep))
    os.makedirs(outdir, exist_ok=True)
    cpt = 0
    ncarnet = (args.ncarnet + args.ncarnet%2)
    max_ = ncarnet * 100
    import datetime
    date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    pbar = tqdm(total=max_//4)
    chunks = np.array_split(np.arange(1, max_//4+1), max((max_)//(30*50), 1))

    for ic, chunk in enumerate(chunks):
        writer = PdfWriter()
        # Generate barcode SVG
        # outp = "{}{}_{}_{}.pdf".format(outdir, str(args.gare), str(args.barcodeprefix), str(i))
        for i in chunk:
            tmp = template_pdf_path
            for j in range(8):
                row, col = j // 2, j % 2
                if col == 0:
                    text_to_encode = "{}{}".format(args.barcodeprefix, str(i+(((max_)//4)*row)).zfill(7))
                    barcode_svg_path = generate_barcode_svg(text_to_encode, barcode_filename)
                    cpt += 1
                output_pdf_path = draw_barcode(barcode_svg_path, tmp, output_pdf_path, row,col)
                # text_to_encode_ = "{}{}".format(args.barcodeprefix, str(i+1).zfill(7))
                # barcode_svg_path = generate_barcode_svg(text_to_encode_, barcode_filename)
                # draw_barcode(barcode_svg_path, output_pdf_path, "{}{}-{}.pdf".format(outdir, text_to_encode, text_to_encode_), 0.48)
                # outp = "{}{}-{}.pdf".format(outdir, text_to_encode, text_to_encode_)
                add_text_to_pdf(output_pdf_path, output_pdf_path, col,row, args.montant, args.annee, args.gare)
                tmp = output_pdf_path
            add_first_page_to_pdf(output_pdf_path, writer)
            pbar.update(1)

        outp =  "{}{}_{}_{}_montant_{}_{}_sur_{}_ncarnet_{}_time_{}.pdf".format(outdir,  "ticket", args.barcodeprefix, args.gare, args.montant, ic+1, len(chunks), ncarnet, date)
        with open(outp, "wb") as output_pdf:
            writer.write(output_pdf)
            # break
            # print(f"PDF with barcode saved as '{output_pdf_path}'")
# from pdfwatermark.src.pdf_watermark.handler import add_watermark_to_pdf
# from pdfwatermark.src.pdf_watermark.options import InsertOptions, DrawingOptions


# import argparse
# import barcode
# from barcode.writer import SVGWriter
# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter, inch
# from reportlab.graphics import renderPDF
# from reportlab.graphics.shapes import Drawing
# import tkinter as tk
# from tkinter import filedialog
# import os
# from svglib.svglib import svg2rlg
# from PyPDF2 import PdfReader, PdfWriter
# import io

# # Function to generate barcode as an SVG
# def generate_barcode_svg(text, filename):
#     code128 = barcode.get('code128', text, writer=SVGWriter())
#     barcode_svg_path = filename
#     code128.save(barcode_svg_path, options={'font_size': 8, "text_distance": 4})  # Save as SVG
#     return barcode_svg_path + ".svg"

# opts = DrawingOptions(
#     watermark="1.png",
#     opacity=1,
#     angle=90,
#     text_color="#000000",
#     text_font="Helvetica",
#     text_size=12,
#     unselectable=False,
#     image_scale=0.8,
#     save_as_image=False,
#     dpi=300,
# )
# y = 0.25
# x = 0.1

# barcode_svg_path=generate_barcode_svg("82100001", "barcode")
# opts_in = InsertOptions(y=y, x=x,horizontal_alignment="center", svg=barcode_svg_path)
# add_watermark_to_pdf("barcode 03.pdf", "output.pdf", opts, opts_in)
# barcode_svg_path=generate_barcode_svg("82100002", "barcode")
# opts_in = InsertOptions(y=y, x=x,horizontal_alignment="center", svg=barcode_svg_path)
# add_watermark_to_pdf("output.pdf", "finale.pdf", opts, opts_in)
