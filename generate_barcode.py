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
from PyPDF2 import PdfReader, PdfWriter
import io

# Function to generate barcode as an SVG
def generate_barcode_svg(text, filename):
    code128 = barcode.get('code128', text, writer=SVGWriter())
    barcode_svg_path = filename
    code128.save(barcode_svg_path)  # Save as SVG
    return barcode_svg_path + ".svg"

# Function to interactively draw a bounding box on a PDF page
def select_bounding_box(pdf_path):
    import fitz
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
# Function to place barcode SVG on a PDF template
def create_pdf_with_barcode(template_pdf_path, barcode_svg_path, output_pdf_path, rect):
    # Read the template PDF
    existing_pdf = PdfReader(open(template_pdf_path, "rb"))
    page = existing_pdf.pages[0]  # Assuming we're working with the first page

    # Create a BytesIO buffer for the new PDF with the barcode
    packet = io.BytesIO()

    # Create a canvas to hold the PDF page with the barcode
    c = canvas.Canvas(packet, pagesize=(page.mediabox.width, page.mediabox.height))

    # Draw the template PDF page onto the canvas
    c.setPageSize((page.mediabox.width, page.mediabox.height))
    
    # Here we directly use `drawImage` method to overlay the template page into the canvas
    c.drawImage(template_pdf_path, 0, 0, page.mediabox.width, page.mediabox.height)

    # Create a Drawing object with the barcode SVG
    barcode_drawing = svg2rlg(barcode_svg_path)

    # Position the barcode in the selected bounding box
    x1, y1, x2, y2 = rect
    barcode_width = x2 - x1
    barcode_height = y2 - y1

    # Adjust the barcode drawing size to fit the bounding box
    barcode_drawing.width = barcode_width
    barcode_drawing.height = barcode_height

    # Draw the barcode on the canvas (positioning based on the bounding box)
    renderPDF.draw(barcode_drawing, c, x1, page.mediabox.height - y2)  # Adjust y-coordinate for PDF's inverted axis

    # Save the canvas with the barcode
    c.save()

    # Move to the beginning of the StringIO buffer
    packet.seek(0)

    # Create a new PDF with the generated barcode
    new_pdf = PdfReader(packet)

    # Create an output PDF to merge the barcode and the template
    output = PdfWriter()

    # Add the original template page to the new PDF
    output.add_page(page)

    # Add the page with barcode placed over the template
    output.add_page(new_pdf.pages[0])

    # Write the output to a real file
    with open(output_pdf_path, "wb") as output_stream:
        output.write(output_stream)

# Main logic
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a barcode and place it on a PDF.")
    parser.add_argument("--text", required=True, help="Text to encode in the barcode")
    parser.add_argument("--output", required=True, help="Path to save the output PDF with the barcode")

    args = parser.parse_args()

    text_to_encode = args.text
    barcode_filename = "barcode_image"
    output_pdf_path = args.output

    # Open file dialog to choose a template PDF
    template_pdf_path = filedialog.askopenfilename(title="Select a PDF Template", filetypes=[("PDF files", "*.pdf")])

    if not template_pdf_path:
        print("No PDF selected. Exiting.")
        exit()

    # Generate barcode SVG
    barcode_svg_path = generate_barcode_svg(text_to_encode, barcode_filename)

    # Select bounding box interactively
    # bounding_box = select_bounding_box(template_pdf_path)
    bounding_box = (159, 100, 267, 125)
    # Create PDF with the generated barcode
    create_pdf_with_barcode(template_pdf_path, barcode_svg_path, output_pdf_path, bounding_box)

    print(f"PDF with barcode saved to {output_pdf_path}")
