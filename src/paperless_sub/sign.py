
#pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org pyhanko[opentype]
import logging
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields,signers
from pyhanko.sign.fields import SigSeedSubFilter
from pyhanko_certvalidator import ValidationContext
from pyhanko import stamp
from pyhanko.pdf_utils import text
from pyhanko.pdf_utils.font import opentype
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from pyhanko.pdf_utils.layout import AxisAlignment, Margins, SimpleBoxLayoutRule
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.stamp import QRPosition,QRStampStyle,QRStamp
from pikepdf import Pdf, Page
from django.conf import settings

logger = logging.getLogger("paperless.bulk_edit")

class SignDocument:
#    CERT_PATH_FILE='../data/certs/cert.p12'
#    CERT_PASSPHRASE=b'l1O!Yutd@XTceY2D'
#    STAMP_FONT='../data/certs/Espera-Regular.ttf'
#    #settings.SCRATCH_DIR
#    MODEL='../data/certs/stamp.pdf'
#    BLANK='../data/certs/blank.pdf'

    zero_margins = SimpleBoxLayoutRule(
        x_align=AxisAlignment.ALIGN_MID,
        y_align=AxisAlignment.ALIGN_MID,
        margins=Margins(5,5,5,5),
    )

    style=stamp.QRStampStyle(
                # Let's include the URL in the stamp text as well
                border_width=0.2,
                background_opacity=0.8,
                stamp_text='Publié le : %(ts)s, par: %(signer)s\nURL: %(url)s\nIntégrité:%(checksum)s\nPage(s): %(currentpage)s/%(totalpage)s ',
                timestamp_format='%D',
                text_box_style=stamp.TextBoxStyle(
                    box_layout_rule=zero_margins,
                    font_size=4,
                ),
                qr_inner_size=12,
    )

    def __init__(self):
        self.meta=self.signatureMeta()
        self.signer=self.createSignerpkcs()

    #récupération des infos du certificat
    @classmethod
    def createSignerpkcs(self):
        signer = signers.SimpleSigner.load_pkcs12(pfx_file=settings.CERT_PATH_FILE, passphrase=settings.CERT_PASSPHRASE) 
        if signer == None:
            print("Error while opening PFX file.")
        return signer

    # Settings for PAdES-LTA
    @classmethod
    def signatureMeta(self):
        signature_meta = signers.PdfSignatureMetadata(
        field_name='Publication', md_algorithm='sha256',
        # Mark the signature as a PAdES signature
        subfilter=SigSeedSubFilter.PADES,
        # We'll also need a validation context
        # to fetch & embed revocation info.
        validation_context=ValidationContext(allow_fetching=True),
        # Embed relevant OCSP responses / CRLs (PAdES-LT)
        embed_validation_info=True,
        # Tell pyHanko to put in an extra DocumentTimeStamp
        # to kick off the PAdES-LTA timestamp chain.
        use_pades_lta=True,
        signer_key_usage={'non_repudiation'},
        )
        return signature_meta

    #Vérification de la présence du champ 
    def verif_already_published(self,inFile):
        with open(inFile, 'rb') as doc:
            r = PdfFileReader(doc)
            if len(r.embedded_signatures) > 0:
                for i in range(len(r.embedded_signatures)):
                    sig = r.embedded_signatures[i]
                    if sig.field_name == "Publication":
                        print(f"champ {sig.field_name} déjà présent ")
                        return True

    #Application de la signature
    def applySignature(self,inFile):
        
        with open(inFile, 'rb+') as inf:
            w = IncrementalPdfFileWriter(inf, strict = False)
            
            fields.append_signature_field(
                #signature invisible
                #w, sig_field_spec=fields.SigFieldSpec('Sign',  box=(50, 20, 170, 50),on_page=0)
                w, sig_field_spec=fields.SigFieldSpec('Publication', empty_field_appearance=1)
            )

            pdf_signer = signers.PdfSigner(
                self.meta, signer=self.signer, stamp_style=self.style
            )
          
            pdf_signer.sign_pdf(
                w, self.signer, in_place=True, appearance_text_params={'url': 'https://example.com/dsklfjsdmlfklsdf/dsmfjskmdfjm','currentpage':'0','totalpage':'1','checksum':'0f12df21sdf154'}
            )
 

    @classmethod
    def page_count(self,inputFile):
        try:
            with open(inputFile,"rb") as doc:
                r=PdfFileReader(doc)
                page_count=(int(r.root['/Pages']['/Count']))
        except:
            print(f"cannot open the file {inputFile}")
        return page_count

    #Application de la signature
    def applyStamp(self,inFile,inUrl,inChecksumValue):

        try: 
            pdfsource = Pdf.open(inFile, allow_overwriting_input=True)    
            total_page=len(pdfsource.pages)

            #on créer un pdf vierge avec autant de page que l'original
            dst = Pdf.new()
            for i in range(total_page):
                print(f"page {i} sur {total_page}")
                dst.add_blank_page()
            dst.save(settings.MODEL)
            dst.close

            with open(settings.MODEL, 'rb+') as model:
                pdf_model = IncrementalPdfFileWriter(model, strict=False)
                #apply stamp from page 1
                for i in range(total_page):
                    mystamp = QRStamp(writer=pdf_model, style=self.style,url="http://exemple.com",text_params={'url': 'https://example.com/dsklfjsdmlfklsdf/dsmfjskmdfjm','signer':'signataire','currentpage':i+1,'totalpage':total_page,'checksum':'0f12df21sdf154'})       
                    mystamp.apply(dest_page=i, x=10, y=10)
                #on créér un modèle avec les stamps à overlay
                pdf_model.write_in_place()


            pdfmodel = Pdf.open(settings.MODEL)
            for i in range(0,total_page):
                destination_page = Page(pdfsource.pages[i])
                thumbnail = Page(pdfmodel.pages[i])
                destination_page.add_overlay(thumbnail)
            pdfmodel.close
            pdfsource.save()
            pdfsource.close

        except Exception as e:
            logger.exception(f"Error to add stamp on document {inFile} : {e}")


#if not myStampTest.verif_already_published("c:/temp/df/essai.pdf"):
#    myStampTest.applyStamp("c:/temp/df/essai.pdf","c:/temp/df/essai_model.pdf")
#    myStampTest.applySignature("c:/temp/df/essai.pdf")



