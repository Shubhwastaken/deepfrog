from pdf2image import convert_from_path

pages = convert_from_path(
    r"C:\Users\shshv\PycharmProjects\hackinf\images\bol_dummy.docx.pdf",
    dpi=300,
    poppler_path=r"C:\poppler-25.12.0\Library\bin"
)

print("Pages:", len(pages))

pages[0].save("debug_page.png", "PNG")