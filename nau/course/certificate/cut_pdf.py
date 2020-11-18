import io, PyPDF2

def cut_pdf_limit_pages(pdf, start:int, end:int):
    '''
    Cut the PDF with a limit number of pages.
    '''
    pdf_reader = PyPDF2.PdfFileReader(io.BytesIO(pdf))
    numPages = pdf_reader.getNumPages()

    if (start == 0 and end == numPages):
        return pdf

    if (start > numPages):
        return None

    end = min(end, numPages)

    pdf_writer = PyPDF2.PdfFileWriter()

    for page in range(start, end):
        pdf_writer.addPage(pdf_reader.getPage(page))

    outputStream = io.BytesIO()
    pdf_writer.write(outputStream)
    binary_pdf = outputStream.getvalue()
    outputStream.close()
    return binary_pdf
