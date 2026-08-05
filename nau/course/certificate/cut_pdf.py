import io, PyPDF2

def cut_pdf_limit_pages(pdf, start:int, end:int):
    '''
    Cut the PDF with a limit number of pages.
    '''
    # PyPDF2.PdfFileReader/PdfFileWriter were fully removed in PyPDF2 3.0.0 and
    # raise PyPDF2.errors.DeprecationError as soon as they're constructed; the
    # non-deprecated equivalents are PdfReader/PdfWriter (same 3.0.1 version
    # pinned in requirements.txt).
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf))
    numPages = len(pdf_reader.pages)

    if (start == 0 and end == numPages):
        return pdf

    if (start > numPages):
        return None

    end = min(end, numPages)

    pdf_writer = PyPDF2.PdfWriter()

    for page in range(start, end):
        pdf_writer.add_page(pdf_reader.pages[page])

    outputStream = io.BytesIO()
    pdf_writer.write(outputStream)
    binary_pdf = outputStream.getvalue()
    outputStream.close()
    return binary_pdf
