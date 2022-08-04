<%! from django.utils.translation import ugettext as _ %>
<%! from django.utils.translation import activate %>
<%! import distutils %>
<%! import re %>
<%
  if content_language is UNDEFINED:
    language = user_language
  else:
    language = content_language
  activate(language)
%>
<%namespace name='static' file='/static_content.html'/>
<%
# set doc language direction
from django.utils.translation import get_language_bidi
dir_rtl = 'rtl' if get_language_bidi() else 'ltr'
course_mode_class = course_mode if course_mode else ''
language_query_string = "language="+language
course_certificate_app_path = request.get_full_path() + ( "?" if "?" not in request.get_full_path() else "&" ) + language_query_string

# Replace the lms with course-certificate on the hostname
course_certificate_host = "//" + request.get_host().replace('lms','course-certificate')

# Uncomment next line for local development
#course_certificate_host = "http://localhost:5000"

#
# Certificate parameters:
#
# document_title: 
#   Title of the document. Eg. "CERTIFICADO"
#
# certificate_description
#   First part of the certificate description. Eg. "Certifica-se que "
#
# accomplishment_copy_description_full
#   Third part of the certificate description, after the person name. Eg. ", concluiu o Curso "
#   
# accomplishment_copy_course_description
#   Fifth part of the certificate description, after the course name. Eg. ", com uma duração estimada de X horas."
#
# 
# location
#   Add a location and date after the certificate main text and before the signatures. Eg. "Lisboa" or "Porto"
#
#
# certificate_background:
#   Link to certificate background, when included it removes the organization logo, course image and name on left panel.
#
# add_course_image_left_panel
#   Add course image on left panel. Defaults to True.
#
# add_course_name_left_panel
#   Add course name on left panel. Defaults to True.
#
# add_organization_logo_to_header
#   Add organization logo on left panel. Defaults to True if the organization has a logo.
#
# accomplishment_copy_course_name
#   Course name
#
# full_course_image_url
#   Replace the course image with a different one.
#
# organization_logo_url
#   Absolute URL to the organization logo. Replace it if you want a different logo for the organization.
#
# organization_logo_max_height 
# organization_logo_max_width
#   Change organization logo max height/width, so streched logos could be increased.
#   
# organization_long_name
#   Name of the organization, defaults to course organization name. Used has image organization logo alt name.
#
# footer_additional_logo
#   Additional logos that the certificate can have between the signatures and founders logos of the NAU platform.
#
# footer_information_color
#    Change footer that includes the date and hash id titles and values from white to other HTML color
#
# footer_information_date_title_color
# footer_information_date_value_color
# footer_information_id_title_color
# footer_information_id_value_color
#    Change specific footer title or value of date or hash id color from white to other HTML color
#
# footer_note_certification_information
#    Change the default NAU disclaimer message
#
# Option for development proposes (False for PROD and True during certificate development):
nau_certificate_issued_display_iframe = False
default_organization_logo_url = ( 'https://' + ( request.get_host().replace('lms.','uploads.static.') if 'fccn.pt' in request.get_host() else 'uploads.static.prod.nau.fccn.pt' ) + '/' + str(organization_logo) ) if len(str(organization_logo))>0 else None
organization_logo_url = context.get('organization_logo_url', default_organization_logo_url )

# Utility function to transform string to uppercase
def uppercase(in_str):
  return in_str.upper()

# Utility function to clean tags on text
CLEANR = re.compile('<.*?>') 
def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

# If need append a space when joining the `current` and the `in_str`
def append_space(current, in_str):
  current_ends_with_text=bool(re.search("[a-zA-Z0-9]$", cleanhtml(current)))
  in_str_starts_with_text=bool(re.search("^[a-zA-Z0-9]", cleanhtml(in_str)))
  if current_ends_with_text and in_str_starts_with_text:
    return current + ' ' + in_str
  else:
    return current + in_str

certificate_require_portuguese_citizen_card=bool(context.get('certificate_require_portuguese_citizen_card', False))
data_exist_from_portuguese_citizen_card= not ( cc_first_name is None or cc_first_name == '' or cc_last_name is None or cc_last_name == '' or cc_nic is None or cc_nic == '' )

# Build `body_text` variable
body_text = ''
body_text = append_space(body_text, context.get('certificate_description', 'Certifica-se que'))
if not showing_data_from_portuguese_citizen_card:
  body_text = append_space(body_text, uppercase(accomplishment_copy_name))
else:
  body_text = append_space(body_text, cc_first_name)
  body_text = append_space(body_text, cc_last_name)
  body_text = append_space(body_text, ", com Cartão Cidadão número ")
  body_text = append_space(body_text, cc_nic)
  if cc_nic_check_digit is not None:
    body_text = append_space(body_text, cc_nic_check_digit)
body_text = append_space(body_text, accomplishment_copy_description_full)
body_text = append_space(body_text, accomplishment_copy_course_name)
body_text = append_space(body_text, accomplishment_copy_course_description)

# side message
certificate_side_message = context.get('certificate_side_message', None)

# footer note certification information message
footer_note_certification_information_default = {
  "pt-pt": "A pessoa mencionada neste certificado completou todas as atividades relativas ao curso em questão. Para mais informações sobre Certificação na plataforma NAU e requisitos para a sua obtenção visite <a target='_blank' href='//nau.edu.pt/sobre/politica-de-certificacao'>nau.edu.pt/sobre/politica-de-certificacao</a>. Este certificado é uma prova de aprendizagem, não tendo qualquer validade formal como prova de qualificação ou como formação conferente de grau.",
  "en": "The person mentioned in this certificate has completed all course activities. For more information about Certification at NAU platform and requirements for obtaining it, please visit <a target='_blank' href='//nau.edu.pt/sobre/politica-de-certificacao'>nau.edu.pt/sobre/politica-de-certificacao</a>. This certificate is an evidence of learning, and has no formal proof of qualification or as a degree that gives a level of education.",
}
footer_note_certification_information = context.get('footer_note_certification_information', footer_note_certification_information_default)
if type(footer_note_certification_information) is dict:
  footer_note_certification_information = footer_note_certification_information.get(language, footer_note_certification_information.get('pt-pt',''))

# Generate a dict with all certificate parameters that students can change,
# so if they change its `name` the print to PDF is forced to be regenerated.
nau_course_certificate_data_dict = {
  "template_version": "v_2020_11_19",
  "language": language,
  "certificate_date_issued": certificate_date_issued,
  "body_text": body_text,
  "footer_note_certification_information": footer_note_certification_information,
}
# Generate a hash of the dict. If the hash changes the print to PDF will
# generate a new file.
import hashlib
import json
nau_course_certificate_version = hashlib.sha1(json.dumps(nau_course_certificate_data_dict, sort_keys=True).encode('utf-8')).hexdigest()
%>

<%
# Show a message to associate portuguese citizen card if on the advanced settings > Certificate Web/HTML View Overrides 
# the field 'certificate_require_portuguese_citizen_card' has the 'true' value.
%>
% if certificate_require_portuguese_citizen_card and ( not data_exist_from_portuguese_citizen_card ):
<!DOCTYPE html>
<html class="no-js" lang="${language}">
  <head dir="${dir_rtl}">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta charset="utf-8">
    <title>${document_title}</title>
  </head>
  <body>
    % if user_language == "pt-pt":
    <p>
      Para visualizar este certificado é necessário que o estudante associe o Cartão de Cidadão Português à sua conta NAU.
    </p>
    <p>
      <a href="https://plataforma-nau.atlassian.net/wiki/spaces/PROD/pages/2042986497/Associar+Cart+o+de+Cidad+o+e+Chave+M+vel+Digital" target="_blank">
        Ajuda para 
        "Associar o Cartão de Cidadão e a Chave Móvel Digital"
        à sua conta NAU.
      </a>
    % else:
    <p>
      To view this certificate, the student must link the Portuguese Citizen Card to their NAU account.
      On this page you can get help on how to
    </p>
    <p>
      <a href="https://plataforma-nau.atlassian.net/wiki/spaces/PROD/pages/2042986497/Associar+Cart+o+de+Cidad+o+e+Chave+M+vel+Digital" target="_blank">
        Help on how to
        "Associate the Portuguese Citizen Card"
        to your NAU account.
      </a>
    </p>
    % endif
  </body>
</html>
% else:
## Print the normal certificate
<!DOCTYPE html>
<html class="no-js" lang="${language}">
<head dir="${dir_rtl}">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta charset="utf-8">
  <meta name="title" property="og:title" content="${document_title}, ${accomplishment_copy_course_name}, ${organization_short_name}">
  <meta name="description" property="og:description" content="${document_meta_description} ${accomplishment_copy_course_name}">
  <meta name="keywords" content="Certificado, ${accomplishment_copy_course_name}, ${organization_short_name}">
  <meta name="author" content="${platform_name}">
  <meta name="viewport" content="width=device-width, initial-scale=1">

  ## Print to PDF on A4 paper on landscape
  <meta name="pdfkit-page-size" content="A4">
  <meta name="pdfkit-orientation" content="Landscape">
  ## Remove any default margins for print to PDF
  <meta name="pdfkit-margin-left" content="0mm" />
  <meta name="pdfkit-margin-right" content="0mm" />
  <meta name="pdfkit-margin-bottom" content="0mm" />
  <meta name="pdfkit-margin-top" content="0mm" />
  ## To fix the PDF printing weren't being printed too small.
  <meta name="pdfkit-zoom" content="2" />
  ## Additional wkhtmltopdf properties that are wrapped by python pdfkit library can be passed to by prefixing them with "pdfkit-" and write them has a new HTTP meta.
  ## The completed list is https://wkhtmltopdf.org/usage/wkhtmltopdf.txt

  <meta name="image" property="og:image" content="https://${ request.get_host().replace('lms','course-certificate') }/image${course_certificate_app_path}" />
  ## Print to PNG Image the og:image
  <meta name="imgkit-format" content="jpeg" />
  <meta name="imgkit-crop-h" content="1025" />
  <meta name="imgkit-zoom" content="1.3" />

  ## This certificate code version. Increase it when changing this code on the LMS.
  <meta name="nau-course-certificate-version" content="${nau_course_certificate_version}">
  ## The filename when downloading the PDF of an issued certificate.
  <meta name="nau-course-certificate-filename" content="certificado-nau-curso-${certificate_id_number}.pdf">
  ## To limit the number of pages that the PDF have.
  <meta name="nau-course-certificate-limit-pages" content="1">

  <title>${document_title}</title>
  <%static:css group='style-certificates'/>
  
  <style>
    /* eduNEXT certificate template asset certificates_styles.css */
    .layout-accomplishment {
        min-width: 1024px;
        height: auto;
        background: #eceff0
    }

    .ednxt-certificate {
        float: none;
        margin-left: auto;
        margin-right: auto;
        position: relative;
        width: 100%;
        max-width: 74rem;
        margin-bottom: 40px;
        padding: 1.25rem;
        background: #fff;
        border-radius: 3px;
        box-shadow: 0 4px 5px 0 rgba(0, 0, 0, .14), 0 1px 10px 0 rgba(0, 0, 0, .12), 0 2px 4px -1px rgba(0, 0, 0, .2);
        overflow: auto
    }

    .ednxt-certificate__vars {
        white-space: pre-line;
        background: #141e1e;
        color: #dce6e6;
        margin: 0 auto;
        font-family: Monaco, Consolas, "Lucida Console", monospace;
        padding: 1em 1em 2.5em;
        line-height: 1.45;
        position: relative;
        overflow-x: scroll
    }

    .ednxt-certificate__vars::-moz-selection {
        color: #141e1e;
        background: #dce6e6
    }

    .ednxt-certificate__vars::selection {
        color: #141e1e;
        background: #dce6e6
    }

    .ednxt-certificate__header {
        display: -webkit-flex;
        display: -ms-flexbox;
        display: flex;
        -webkit-justify-content: space-between;
        -ms-flex-pack: justify;
        justify-content: space-between;
        -webkit-align-items: center;
        -ms-flex-align: center;
        align-items: center;
        width: 100%;
        float: left;
        padding-left: .625rem;
        padding-right: .625rem
    }

    @media screen and (min-width:40em) {
        .ednxt-certificate__header {
            padding-left: .9375rem;
            padding-right: .9375rem
        }
    }

    .ednxt-certificate__content-course:last-child:not(:first-child),
    .ednxt-certificate__content-description:last-child:not(:first-child),
    .ednxt-certificate__content-detail:last-child:not(:first-child),
    .ednxt-certificate__content-recipient:last-child:not(:first-child),
    .ednxt-certificate__content-summary:last-child:not(:first-child),
    .ednxt-certificate__content:last-child:not(:first-child),
    .ednxt-certificate__footer-information:last-child:not(:first-child),
    .ednxt-certificate__footer-information_date:last-child:not(:first-child),
    .ednxt-certificate__footer-information_id:last-child:not(:first-child),
    .ednxt-certificate__footer-information_logo:last-child:not(:first-child),
    .ednxt-certificate__footer-link:last-child:not(:first-child),
    .ednxt-certificate__footer-signatories:last-child:not(:first-child),
    .ednxt-certificate__footer-signatures:last-child:not(:first-child),
    .ednxt-certificate__footer:last-child:not(:first-child),
    .ednxt-certificate__header-logo:last-child:not(:first-child),
    .ednxt-certificate__header-title:last-child:not(:first-child),
    .ednxt-certificate__header:last-child:not(:first-child) {
        float: right
    }

    .ednxt-certificate__header-title {
        width: 33.33333%;
        float: left;
        padding-left: .625rem;
        padding-right: .625rem;
        color: #0079bc;
        font-size: 48px;
        font-weight: 300;
        line-height: 1.1;
        text-transform: uppercase
    }

    @media screen and (min-width:40em) {
        .ednxt-certificate__header-title {
            padding-left: .9375rem;
            padding-right: .9375rem
        }
    }

    .ednxt-certificate__header-logo {
        width: 50%;
        float: left;
        padding-left: .625rem;
        padding-right: .625rem
    }

    @media screen and (min-width:40em) {
        .ednxt-certificate__header-logo {
            padding-left: .9375rem;
            padding-right: .9375rem
        }
    }

    .ednxt-certificate__header-logo a {
        float: right;
        transition: none;
        max-width: 100%;
        border-bottom: 0
    }

    .ednxt-certificate__header-logo a:active,
    .ednxt-certificate__header-logo a:focus,
    .ednxt-certificate__header-logo a:hover {
        border-bottom: 0
    }

    .ednxt-certificate__header-logo img {
        min-width: 64px;
        max-width: 100%;
        min-height: 64px;
        max-height: 124px
    }

    .ednxt-certificate__content {
        width: 100%;
        float: left;
        padding-left: .625rem;
        padding-right: .625rem;
        margin: 12px 0;
        padding: 40px
    }

    @media screen and (min-width:40em) {
        .ednxt-certificate__content {
            padding-left: .9375rem;
            padding-right: .9375rem
        }
    }

    .ednxt-certificate__content-course,
    .ednxt-certificate__content-description,
    .ednxt-certificate__content-detail,
    .ednxt-certificate__content-recipient,
    .ednxt-certificate__content-summary {
        width: 100%;
        float: left;
        padding-left: .625rem;
        padding-right: .625rem;
        margin-bottom: 20px
    }

    @media screen and (min-width:40em) {
        .ednxt-certificate__content-course,
        .ednxt-certificate__content-description,
        .ednxt-certificate__content-detail,
        .ednxt-certificate__content-recipient,
        .ednxt-certificate__content-summary {
            padding-left: .9375rem;
            padding-right: .9375rem
        }
    }

    .ednxt-certificate__content-description,
    .ednxt-certificate__content-detail,
    .ednxt-certificate__content-summary {
        font-size: 18px;
        line-height: 1.6
    }

    .ednxt-certificate__content-course,
    .ednxt-certificate__content-recipient {
        color: #000;
        font-weight: 600;
        line-height: 1.2
    }

    .ednxt-certificate__content-recipient {
        font-size: 40px
    }

    .ednxt-certificate__content-course {
        font-size: 28px
    }

    .ednxt-certificate__footer {
        display: -webkit-flex;
        display: -ms-flexbox;
        display: flex;
        -webkit-justify-content: space-between;
        -ms-flex-pack: justify;
        justify-content: space-between;
        -webkit-align-items: center;
        -ms-flex-align: center;
        align-items: center;
        width: 100%;
        float: left;
        padding-left: .625rem;
        padding-right: .625rem;
        -webkit-flex-wrap: wrap;
        -ms-flex-wrap: wrap;
        flex-wrap: wrap
    }

    @media screen and (min-width:40em) {
        .ednxt-certificate__footer {
            padding-left: .9375rem;
            padding-right: .9375rem
        }
    }

    .ednxt-certificate__footer-signatures {
        width: 66.66667%;
        float: left;
        padding-left: .625rem;
        padding-right: .625rem
    }

    @media screen and (min-width:40em) {
        .ednxt-certificate__footer-signatures {
            padding-left: .9375rem;
            padding-right: .9375rem
        }
    }

    .ednxt-certificate__footer-signatories {
        width: 100%;
        float: left;
        padding-left: .625rem;
        padding-right: .625rem;
        text-align: center
    }

    @media screen and (min-width:40em) {
        .ednxt-certificate__footer-signatories {
            padding-left: .9375rem;
            padding-right: .9375rem
        }
    }

    .ednxt-certificate__footer-signatory {
        float: none;
        display: inline-block;
        vertical-align: middle;
        width: 32%;
        padding-left: .9375rem;
        padding-right: .9375rem
    }

    .ednxt-certificate__footer-signatory_signature {
        display: block;
        max-width: 100%;
        max-height: 6.25rem;
        margin: 0 auto;
        padding: 1.25rem .625rem
    }

    .ednxt-certificate__footer-signatory_name {
        margin-bottom: .3125rem;
        font-size: .875rem;
        font-weight: 600;
        line-height: 1.6
    }

    .ednxt-certificate__footer-signatory_credentials {
        font-size: .75rem;
        line-height: 1.5
    }

    .ednxt-certificate__footer-signatory_credentials .role {
        white-space: pre-line
    }

    .ednxt-certificate__footer-signatory_credentials .organization {
        display: block;
        margin-top: .3125rem;
        font-style: italic
    }

    .ednxt-certificate__footer-information {
        width: 33.33333%;
        float: left;
        padding-left: .625rem;
        padding-right: .625rem
    }

    @media screen and (min-width:40em) {
        .ednxt-certificate__footer-information {
            padding-left: .9375rem;
            padding-right: .9375rem
        }
    }

    .ednxt-certificate__footer-information_logo {
        width: 100%;
        float: left;
        padding-left: .625rem;
        padding-right: .625rem;
        margin-bottom: 16px
    }

    @media screen and (min-width:40em) {
        .ednxt-certificate__footer-information_logo {
            padding-left: .9375rem;
            padding-right: .9375rem
        }
    }

    .ednxt-certificate__footer-information_logo img {
        float: right;
        max-width: 124px;
        margin-top: 2px
    }

    .ednxt-certificate__side_message {
      position: absolute;
      bottom: 4cm;
      font-weight: 700;
      font-size: 12px;
      width: 7cm;
      line-height: 1.5;
    }

    .ednxt-certificate__footer-information_date,
    .ednxt-certificate__footer-information_id {
        width: 100%;
        float: left;
        padding-left: .625rem;
        padding-right: .625rem;
        margin-bottom: 10px;
        text-align: right
    }

    @media screen and (min-width:40em) {
        .ednxt-certificate__footer-information_date,
        .ednxt-certificate__footer-information_id {
            padding-left: .9375rem;
            padding-right: .9375rem
        }
    }

    .ednxt-certificate__footer-information_date span,
    .ednxt-certificate__footer-information_id span {
        display: block;
        margin-bottom: 0;
        font-size: 12px;
        font-weight: 600
    }

    .ednxt-certificate__footer-information_date .title,
    .ednxt-certificate__footer-information_id .title {
        color: #a7a4a4;
        text-transform: uppercase;
        line-height: 1.5;
        letter-spacing: .03125rem
    }

    .ednxt-certificate__footer-information_date .value,
    .ednxt-certificate__footer-information_id .value {
        color: #6b6969;
        font-weight: 700
    }

    .ednxt-certificate__footer-link {
        width: 100%;
        float: left;
        padding-left: .625rem;
        padding-right: .625rem;
        -webkit-flex: 0 0 100%;
        -ms-flex: 0 0 100%;
        flex: 0 0 100%;
        max-width: 100%;
        display: none;
        margin-top: 16px;
        text-align: center;
        font-size: 12px
    }

    @media screen and (min-width:40em) {
        .ednxt-certificate__footer-link {
            padding-left: .9375rem;
            padding-right: .9375rem
        }
    }

    @media print {
        body {
            margin: 1.875rem 1.875rem 0!important
        }
        .ednxt-certificate {
            margin-bottom: 0;
            padding: 1px 10px;
            box-shadow: none
        }
        .ednxt-certificate__header-title {
            width: 50%;
            font-size: 32px
        }
        .ednxt-certificate__header__header-logo img {
            max-height: 86px
        }
        .ednxt-certificate__content {
            padding: 16px
        }
        .ednxt-certificate__content-recipient {
            font-size: 36px
        }
        .ednxt-certificate__content-course {
            font-size: 26px
        }
        .ednxt-certificate__footer-information_logo img {
            max-width: 124px!important
        }
        .ednxt-certificate__footer-link {
            display: block
        }
    }

    @page {
        margin-left: 0;
        margin-right: 0;
        margin-top: 0;
        margin-bottom: 0
    }

    @media (max-width:1024px) {
        .message-block {
            width: 100%
        }
    }
  </style>

  <style>
    /* Custom NAU template styles */

    @page {
      size: A4 landscape;
      margin: 0mm 0mm 0mm 0mm;
    }

    @media print {
      body {
        margin: 0 !important;
      }

      .sr-only {
        display: none;
      }

      .wrapper-about {
        display: none;
      }

      .ednxt-certificate {
        margin-left: 0px;
        margin-right: 0px;
      }
    }

    @media all {
      .ednxt-certificate__side_message {
        color: ${context.get('certificate_side_message_color', context.get('footer_information_color', 'white'))};
      }
      .ednxt-certificate__footer-information_date .title {
        color: ${context.get('footer_information_date_title_color', context.get('footer_information_color', 'white'))};
      }
      .ednxt-certificate__footer-information_date .value {
        color: ${context.get('footer_information_date_value_color', context.get('footer_information_color', 'white'))};
      }
      .ednxt-certificate__footer-information_id .title {
        color: ${context.get('footer_information_id_title_color', context.get('footer_information_color', 'white'))};
      }
      .ednxt-certificate__footer-information_id .value {
      }
      .ednxt-certificate__footer-information_id a {
        color: ${context.get('footer_information_id_value_color', context.get('footer_information_color', 'white'))};
      }
      .ednxt-certificate__footer-information {
        position: absolute;
        left: -1cm;
        bottom: 0.8cm;
        z-index: 1;
      }
      .ednxt-certificate__footer-certification-information {
        position: absolute;
        bottom: 0.5cm;
        left: 9.5cm;
        width: auto;
        display: block;
        margin-top: 0px;
        font-size: 9px;
        padding-right: 10px;
      }
      .ednxt-certificate__footer-link {
          position: absolute;
          bottom: 15.5cm;
          left: 22cm;
          width: 500px;
          display: block;
          margin-top: 0px;
          -webkit-transform: rotate(270deg);
          -moz-transform: rotate(270deg);
          -o-transform: rotate(270deg);
          -ms-transform: rotate(270deg);
          transform: rotate(270deg);
          font-size: 9px;
      }
      .linkedin-button {
        margin-top: 24px;
        margin-bottom: 0;
      }
      .edxnt-certificate {
        display: block;
        position: relative;
      }
      .ednxt-certificate__content {
        top: 0em;
        position: relative;
        z-index: 1;
      }
      .certificate-background {
        position: absolute;
        top: 0cm;
        left: 0cm;
        width: 29cm;
        height: 21cm;
        z-index: 0;
      }
      .ednxt-certificate {
        min-height: 21cm;
        max-height: 21cm;
        min-width: 29cm;
        max-width: 29cm;
      }
      .nau-logo-funders {
        max-width: 9cm !important;
        position: absolute;
        left: 9.8cm;
        bottom: 1.5cm;
      }
      .nau-logo {
        max-height: 2cm;
        position: absolute;
        right: 0.7cm;
        top: 1cm;
      }
      .cert-footer-rp {
        height: 4em;
        position: absolute;
        bottom: 2em;
      }
      .cert-footer-rp img {
        height: 100%;
      }
     .cert-left {
        position: absolute;
        top: 6cm;
        left: 10cm;
        width: 18cm;
        text-align: justify;
        z-index: 1;
      }
      .cert-right {
        width: 8.8cm;
        padding: 1cm;
        position: absolute;
        left: 0cm;
        top: 10cm;
        font-size: 22pt;
        z-index: 1;
        color: white;
        text-align: center;
      }
      .ednxt-certificate__header-title {
        font-weight: bold;
        position: absolute;
        top: 4cm;
        left: 11cm;
        width: 17cm;
        text-align: center;
        z-index: 1;
        color: black;
      }
      .cert-text {
        font-size: 1.1rem;
        line-height: 1.5em;
      }
      p.cert-text.name {
        font-weight: bold;
        text-align: center;
        font-size: 2em;
      }
      ul {
        margin-left: 0;
      }
      .ednxt-certificate__footer-signatories {
        position: absolute;
        top: 10.5cm;
        left: 10cm;
        text-align: center;
        width: 18cm;
        z-index: 1;
      }
      .course-image {
        max-height: 8cm;
        position: absolute;
        left: 0.8cm;
        top: 4cm;
        max-width: 6.7cm !important;
        padding: 0.5cm;
        background-color: white;
        border-radius: 25px;
      }
      .left-panel-course-name {
        max-height: 8cm;
        position: absolute;
        left: 0.8cm;
        top: 1cm;
        max-width: 7.3cm;
        color: white;
        font-size: 20px;
      }
      .organization-logo {
        max-height: ${context.get('organization_logo_max_height', '1.5cm')};
        position: absolute;
        left: 10cm;
        top: 1.2cm;
        max-width: ${context.get('organization_logo_max_width', '13cm')};
      }
      .footer-additional-logo {
        max-width: 18cm !important;
        position: absolute;
        left: 9.8cm;
        bottom: 3cm;
        max-height: 2.7cm;
      }
      .wrapper-banner-user {
        margin-top: 0px;
      }
    }
  </style>
  <%static:optional_include_mako file="cert-head-extra.html" is_theming_enabled="True" />
</head>
  <body class="layout-accomplishment view-valid-accomplishment ${dir_rtl} certificate certificate-${course_mode_class} ednxt-certificate__container" data-view="valid-accomplishment">
    <div class="wrapper-view" dir="${dir_rtl}">
      <hr class="divider sr-only">
      % if user.is_authenticated and user.id == int(accomplishment_user_id):
        <%include file="/certificates/_accomplishment-banner.html" />
      % endif

      % if nau_certificate_issued_display_iframe and request.GET.get('preview') is None and request.META.get('HTTP_X_NAU_CERTIFICATE_FORCE_HTML') is None:
        <iframe id="certificateToPdfIframe" src="${course_certificate_host}/inline${course_certificate_app_path}" 
          style="width: 1px; min-width: 100%; min-height: 100%; height: 870px;">
        </iframe>
      % else:
        <div class="ednxt-container">
          <div class="ednxt-certificate">
            
            <div class="ednxt-certificate__header">
              <div class="ednxt-certificate__header-logo" style="width: 100%;">                
              </div>
            </div>
            <h1 class="ednxt-certificate__header-title">${document_title}</h1>
            <div class="cert-left">
              <p class="cert-text">
                ${body_text}
              </p>
              % if context.get('location'):
                <p class="cert-text right">${location}, ${certificate_date_issued}</p>
              % endif
            </div>
            <div class="cert-right">
              ${context.get('left_msg', '')}
            </div>
            <div class="signatures">
              <div class="ednxt-certificate__footer-signatures">
                % if mode != 'base':
                  <h3 class="sr-only">${_("Noted by")}</h3>
                  <div class="ednxt-certificate__footer-signatories">
                    % if certificate_data:
                      % for signatory in certificate_data.get('signatories', []):
                        % if signatory['name'] != "":
                          ## display: flex isn't working on wkhtmltopdf and wkhtmltoimage so an old width with percentage works
                          <div class="ednxt-certificate__footer-signatory" style="width: ${ 100/len(certificate_data.get('signatories', [])) -1 }%;">
                            % if signatory['signature_image_path'] != "":
                              <img class="ednxt-certificate__footer-signatory_signature" src="${static.url(signatory['signature_image_path'])}" alt="${signatory['name']}">
                            % endif
                            <p class="ednxt-certificate__footer-signatory_credentials">
                              <span class="signatory">${ "(" if signatory['signature_image_path'] != "" else "" }${signatory['name']}${ ")" if signatory['signature_image_path'] != "" else "" }</span><br/>
                              <span class="role">${signatory['title']}</span>
                              <span class="organization">${signatory['organization']}</span>
                            </p>
                          </div>
                        % endif
                      % endfor
                    % endif
                  </div>
                % endif
              </div>
            </div>
            <div class="ednxt-certificate__footer">

              % if certificate_background is UNDEFINED:
                <img class="certificate-background" src="${static.certificate_asset_url('nau-certificado-background')}">
              % else:
                <img class="certificate-background" src="${certificate_background}">
              % endif

              <img class="nau-logo" src="${static.certificate_asset_url('nau-logo-certificado')}" alt="Logo da Plataforma NAU - Sempre a Aprender">
              % if bool(distutils.util.strtobool(context.get('add_course_image_left_panel', 'true'))):
                <img class="course-image" src="${full_course_image_url}" alt="Imagem do curso">
              % endif

              % if bool(distutils.util.strtobool(context.get('add_course_name_left_panel', 'true'))):
              <div class="left-panel-course-name">
                ${accomplishment_copy_course_name}
              </div>
              % endif

              % if bool(distutils.util.strtobool(context.get('add_organization_logo_to_header', 'true'))) and organization_logo_url:
                <img class="organization-logo" src="${organization_logo_url}" alt="${organization_long_name}">
              % endif
              
              % if context.get('footer_additional_logo'):
                <img class="footer-additional-logo" src="${footer_additional_logo}">
              % endif

              <img class="nau-logo-funders" src="${static.certificate_asset_url('3logos-financiadores-portugal-2020-compete-feder')}" alt="Logos das entidades financiadoras">

              % if certificate_side_message:
              <div class="ednxt-certificate__side_message">
                  ${certificate_side_message}
              </div>
              % endif

              <div class="ednxt-certificate__footer-information">
                <div class="ednxt-certificate__footer-information_logo">
                  <h3 class="sr-only">${_("Supported by the following organizations")}</h3>
                </div>
                <div class="ednxt-certificate__footer-information_date">
                  <span class="title">${certificate_date_issued_title}</span>
                  <span class="value">${certificate_date_issued}</span>
                </div>
                <div class="ednxt-certificate__footer-information_id">
                  <span class="title">${certificate_id_number_title}${certificate_id_number_separator if certificate_id_number_separator else ':'}</span>
                  <span class="value"><a href="/certificates/${certificate_id_number}">${certificate_id_number}</a></span>
                </div>
              </div>
              <div class="ednxt-certificate__footer-link">
                <a href="https://lms.nau.edu.pt/certificates/${certificate_id_number}">https://lms.nau.edu.pt/certificates/${certificate_id_number}</a>
              </div>
              <div class="ednxt-certificate__footer-certification-information">
                ${footer_note_certification_information}
              </div>
            </div>
          </div>
        </div>
      % endif
      <div class="wrapper-about"></div>
    </div>

    % if request.GET.get('preview') is None and request.META.get('HTTP_X_NAU_CERTIFICATE_FORCE_HTML') is None:
      <script type="text/javascript">

        // commented code that replace the browser print with a call to download certificate has PDF.
        function printView(event) {
          window.location.assign("${course_certificate_host}/attachment${course_certificate_app_path}");
        }
        document.getElementById("action-print-view").onclick = printView;
      </script>
    % else:
      <%include file="/certificates/_assets-secondary.html" />
    % endif

    %if badge:
      <%include file="/certificates/_badges-modal.html" />
    %endif

  </body>
</html>
% endif