import string 
import random
from django.utils.text import slugify 


""" unique slug generator: 
    - basically if there are more than one stories with the same title, generator generates a different slug for the other one """
    
def random_string_generator(size = 10, chars = string.ascii_lowercase + string.digits): 
    return ''.join(random.choice(chars) for _ in range(size)) 
  
def unique_slug_generator(instance, new_slug = None): 
    if new_slug is not None: 
        slug = new_slug 
    else: 
        slug = slugify(instance.title) 
    Klass = instance.__class__ 
    qs_exists = Klass.objects.filter(slug = slug).exists() 
      
    if qs_exists: 
        new_slug = "{slug}-{randstr}".format( 
            slug = slug, randstr = random_string_generator(size = 4)) 
              
        return unique_slug_generator(instance, new_slug = new_slug) 
    return slug 

def unique_slug_generator_for_entry(instance, new_slug = None): 
    if new_slug is not None: 
        slug = new_slug 
    else: 
        slug = "{randstr}".format( 
            randstr = random_string_generator(size = 9)) 
    Klass = instance.__class__ 
    qs_exists = Klass.objects.filter(slug = slug).exists() 
      
    if qs_exists: 
        new_slug = "{randstr}".format( 
            randstr = random_string_generator(size = 9)) 
              
        return unique_slug_generator_for_entry(instance, new_slug = new_slug) 
    return slug 



""" PDF CLASS FOR STORY_DOWNLOAD """

from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER

PAGESIZE = (140 * mm, 216 * mm)
BASE_MARGIN = 5 * mm

class PdfCreator:    
    def add_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setTitle(self.title)
        canvas.setSubject("A fascinating story written in the Storio")
        canvas.setFont('Times-Roman', 10)
        page_number_text = "%d" % (doc.page)
        canvas.drawCentredString(
            0.75 * inch,
            0.75 * inch,
            page_number_text
        )
        canvas.restoreState()    

    def get_body_style(self):
        sample_style_sheet = getSampleStyleSheet()
        body_style = sample_style_sheet['BodyText']
        body_style.fontSize = 6
        body_style.firstLineIndent = 24
        body_style.fontName = "Verdana"
        body_style.splitLongWords = True
        return body_style    

    def get_title_style(self):
        sample_style_sheet = getSampleStyleSheet()
        title_style = sample_style_sheet['Heading1']
        title_style.fontSize = 9
        title_style.fontName = "Verdana"
        title_style.splitLongWords = True
        title_style.alignment=TA_CENTER
        return title_style    

    def build_pdf(self, title, text):
        pdf_buffer = BytesIO()
        my_doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=PAGESIZE,
            topMargin=BASE_MARGIN*3,
            leftMargin=BASE_MARGIN,
            rightMargin=BASE_MARGIN,
            bottomMargin=BASE_MARGIN*2
        )        

        pdfmetrics.registerFont(TTFont('Verdana', 'Verdana.ttf'))

        body_style = self.get_body_style() 
        title_style = self.get_title_style()
        self.title = title     

        flowables = [
            Paragraph(title, title_style),
            Paragraph(text, body_style)
        ]        

        my_doc.build(
            flowables,
            onFirstPage=self.add_page_number,
            onLaterPages=self.add_page_number,
        )        

        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_value