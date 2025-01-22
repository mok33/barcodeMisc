import os
import datetime
import numpy as np
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import fitz  # PyMuPDF for handling PDFs
from license import generate_barcode_svg, draw_barcode, add_text_to_pdf
from test import add_first_page_to_pdf
from PyPDF2 import PdfReader, PdfWriter

def process_chunk(params):
    iw, chunk, args, max_items, template_pdf_path, barcode_filename, outdir = params
    output_files = []
    writer = PdfWriter()
    barcode_filename = '{}_{}'.format(barcode_filename, iw)
    for i in tqdm(chunk):
        tmp = template_pdf_path
        output_pdf_path =  args.output.replace(".pdf",  "_{}.pdf".format(iw))
        for j in range(4 * 3):
            row, col = j // 3, j % 3
            if col == 0:
                text_to_encode = f"{args.barcodeprefix}{str(i + (((max_items) // 4) * row)).zfill(7)}"
                barcode_svg_path = generate_barcode_svg(text_to_encode, barcode_filename)
            output_pdf_path = draw_barcode(barcode_svg_path, tmp, output_pdf_path, row, col)
            add_text_to_pdf(output_pdf_path, output_pdf_path, col, row, args.montant, args.annee, args.gare)
            tmp = output_pdf_path
        add_first_page_to_pdf(output_pdf_path, writer)

    # Combine processed PDFs for this chunk
    if len(chunk) > 0:
        chunk_output = f"{outdir}chunk_{chunk[0]}_to_{chunk[-1]}.pdf"
        with open(chunk_output, "wb") as output_pdf:
                writer.write(output_pdf)
    # merge_pdfs(output_files, chunk_output)
        return chunk_output

def merge_pdfs(pdf_paths, output_path):
    """Merge multiple PDFs into a single PDF using fitz."""
    doc = fitz.open()
    for pdf_path in pdf_paths:
        src_doc = fitz.open(pdf_path)
        for page in src_doc:
            doc.insert_pdf(src_doc, from_page=page.number, to_page=page.number)
        src_doc.close()
    doc.save(output_path)
    doc.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate a barcode and place it on a PDF.")
    parser.add_argument("--pdftemplate", required=True, help="Path to save the output PDF with the barcode")
    parser.add_argument("--gare", required=True, help="Path to save the output PDF with the barcode")
    parser.add_argument("--annee", required=True, help="Path to save the output PDF with the barcode")
    parser.add_argument("--montant", type=str, default="", help="Path to save the output PDF with the barcode")
    parser.add_argument("--barcodeprefix", required=True, help="Text to encode in the barcode")
    parser.add_argument("--output", default='res.pdf', help="Path to save the output PDF with the barcode")
    parser.add_argument("--min", type=int, default=1, help="Path to save the output PDF with the barcode")
    parser.add_argument("--max", type=int, default=50, help="Path to save the output PDF with the barcode")
    parser.add_argument("--ncarnet", type=int, default=50, help="Path to save the output PDF with the barcode")
    parser.add_argument("--carnet25", default=False, action='store_true')
    parser.add_argument("--carnet100", default=False, action='store_true')

    args = parser.parse_args()

    template_pdf_path = args.pdftemplate
    outdir = os.path.join("output", "licenses", f"{args.gare}-{args.barcodeprefix}/")
    tmpdir = os.path.join("./tmp/", "licenses", f"{args.gare}-{args.barcodeprefix}/")
    os.makedirs(tmpdir, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    ncarnet = (args.ncarnet + args.ncarnet%2)
    if args.carnet25:
        ncarnet = int(np.ceil(ncarnet / 4) * 4)

    # ncarnet = args.ncarnet
    max_items = ncarnet * (25 if args.carnet25 else 100 if args.carnet100 else 100)
    # max_items = args.min+max_items
    chunks = np.array_split(args.min + np.arange(0, max_items // 4), cpu_count())
    
    # process_chunk((0, chunks[0], args, template_pdf_path, "barcode_image", tmpdir))
    # Use multiprocessing Pool to parallelize
    with Pool(processes=cpu_count()) as pool:
        results = list(pool.map(
            process_chunk,
            [(iw, chunk, args, max_items, template_pdf_path, "barcode_image", tmpdir) for iw, chunk in enumerate(chunks)]
        ))

    # Combine all chunk outputs into a final PDF
    final_output =  "{}{}_{}_{}_{}_montant_{}_ncarnet_{}.pdf".format(outdir,  "license", os.path.splitext(os.path.basename(args.pdftemplate))[0], args.barcodeprefix, args.gare, args.montant, ncarnet)
    if args.carnet25:
        final_output = final_output.replace(".pdf", "_carnet25.pdf")
    merge_pdfs(results, final_output)
    print(f"Final PDF saved at: {final_output}")
