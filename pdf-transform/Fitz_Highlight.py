import fitz
from fitz.utils import getColor
aliceblue = getColor("BLUE")

doc = fitz.open("")
inst_counter = 0
for pi in range(doc.pageCount):
    page = doc[pi]

    text = "Lorem isupum sentence"
    text2 = "isupum"
    text_instances = page.searchFor(text)
    text_instances2 = page.searchFor(text2)

    five_percent_height = (page.rect.br.y - page.rect.tl.y)*0.05

    for inst in text_instances:
        inst_counter += 1
        highlight = page.addHighlightAnnot(inst)

        # define a suitable cropping box which spans the whole page 
        # and adds padding around the highlighted text
        # tl_pt = fitz.Point(page.rect.tl.x, max(page.rect.tl.y, inst.tl.y - five_percent_height))
        # br_pt = fitz.Point(page.rect.br.x, min(page.rect.br.y, inst.br.y + five_percent_height))
        # hl_clip = fitz.Rect(tl_pt, br_pt)

        # zoom_mat = fitz.Matrix(2, 2)
        # pix = page.getPixmap(matrix=zoom_mat, clip = hl_clip)
        # pix.writePNG(f"pg{pi}-hl{inst_counter}.png")


    for inst in text_instances2:
        inst_counter += 1
        highlight = page.addHighlightAnnot(inst)    
        color = {"stroke": (1,0,0)}
        highlight.setColors(color)
        highlight.update()

        # define a suitable cropping box which spans the whole page 
        # and adds padding around the highlighted text
        # tl_pt = fitz.Point(page.rect.tl.x, max(page.rect.tl.y, inst.tl.y - five_percent_height))
        # br_pt = fitz.Point(page.rect.br.x, min(page.rect.br.y, inst.br.y + five_percent_height))
        # hl_clip = fitz.Rect(tl_pt, br_pt)

        # zoom_mat = fitz.Matrix(2, 2)
        # pix = page.getPixmap(matrix=zoom_mat, clip = hl_clip)
        # pix.writePNG(f"pg{pi}-hl{inst_counter}.png")


doc.save('')