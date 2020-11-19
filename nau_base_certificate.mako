<%! from django.utils.translation import ugettext as _ %>
<%! from django.utils.translation import activate %>
<%
  activate(user_language)
%>
<%namespace name='static' file='/static_content.html'/>
<%
# set doc language direction
from django.utils.translation import get_language_bidi
dir_rtl = 'rtl' if get_language_bidi() else 'ltr'
course_mode_class = course_mode if course_mode else ''

#
# Certificate parameters:
#
# document_title: 
#   Title of the document. Eg. "CERTIFICADO"
#
# certificate_description
#   First part of the certificate description. Eg. "Certificate que"
#
# accomplishment_copy_description_full
#   Third part of the certificate description, after the person name. Eg. ", concluiu o Curso "
#   
# accomplishment_copy_course_description
#   Fift part of the certificate description, after the course name. Eg. ", com uma duração estimada de X horas."
#
#
#
#
# certificate_background:
#   Link to certificate background, when included it removes the organization logo, course image and name on left panel.
#
# force_add_course_image_left_panel
#   Force add course image on left panel even with different certificate background.
#
# force_add_course_name_left_panel
#   Force add course name on left panel even with different certificate background.
#
# force_add_organization_logo_to_header
#   Force add organization logo on left panel even with different certificate background.
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
#
# Option for development proposes (False for PROD and True during certificate development):
nau_certificate_issued_display_iframe = False

organization_logo_url = ( 'https://' + ( request.get_host().replace('lms.','uploads.static.') if 'fccn.pt' in request.get_host() else 'uploads.static.prod.nau.fccn.pt' ) + '/' + str(organization_logo) ) if len(str(organization_logo))>0 else None
%>
<!DOCTYPE html>
<html class="no-js" lang="${user_language}">
<head dir="${dir_rtl}">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta charset="utf-8">
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

  ## This certificate code version. Increase it when changing this code on the LMS.
  <meta name="nau-course-certificate-version" content="certificate_template_version_2020_11_16_3_certificate_date_${certificate_date_issued}">

  ## The filename when downloading the PDF of an issued certificate.
  <meta name="nau-course-certificate-filename" content="certificado-nau-curso-${course_id}.pdf">

  ## To limit the number of pages that the PDF have.
  <meta name="nau-course-certificate-limit-pages" content="1">

  <title>${document_title}</title>
  <%static:css group='style-certificates'/>
  <link rel="stylesheet" type="text/css" href="${static.certificate_asset_url('certificates-styles')}">
  <style>
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
      .ednxt-certificate__footer-information_date .title {
        color: ${context.get('footer_information_date_title_color', 'white')};
      }
      .ednxt-certificate__footer-information_date .value {
        color: ${context.get('footer_information_date_value_color', 'white')};
      }
      .ednxt-certificate__footer-information_id .title {
        color: ${context.get('footer_information_id_title_color', 'white')};
      }
      .ednxt-certificate__footer-information_id .value {
        color: ${context.get('footer_information_id_value_color', 'white')};
      }
      .ednxt-certificate__footer-information_id a {
        color: white;
      }
      .ednxt-certificate__footer-information {
        position: absolute;
        left: -1cm;
        bottom: 0.8cm;
        z-index: 1;
        color: ${context.get('footer_information_color', 'white')};
      }
      .ednxt-certificate__footer-link {
        position: absolute;
        bottom: 1cm;
        left: 9.5cm;
        width: auto;
        display: block;
        margin-top: 0px;
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
        font-size: 1.2em;
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
      .ednxt-certificate__footer-signatory {
        width: 100%;
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
    }
  </style>
  <%static:optional_include_mako file="cert-head-extra.html" is_theming_enabled="True" />
</head>
  <body class="layout-accomplishment view-valid-accomplishment ${dir_rtl} certificate certificate-${course_mode_class} ednxt-certificate__container" data-view="valid-accomplishment">
    <div class="wrapper-view" dir="${dir_rtl}">
      <hr class="divider sr-only">
      % if user.is_authenticated() and user.id == int(accomplishment_user_id):
        <%include file="/certificates/_accomplishment-banner.html" />
        <div class="wrapper-banner wrapper-banner-user">
          <section class="banner banner-user">
            <div class="message message-block message-notice">
              <div class="wrapper-copy-and-actions">
                <div class="message-actions">
                </div>
              </div>
            </div>
          </section>
        </div>
      % endif

      % if nau_certificate_issued_display_iframe and request.GET.get('preview') is None and request.META.get('HTTP_X_NAU_CERTIFICATE_FORCE_HTML') is None:

        ## Replace http://localhost:5000 with //${ request.get_host().replace('lms','course-certificate') }
        <iframe id="certificateToPdfIframe" src="//${ request.get_host().replace('lms','course-certificate') }/inline${request.META.get('RAW_URI')}" 
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
                <%
                def uppercase(in_str):
                  return str(in_str).upper()
                %>
                ${certificate_description}
                % if cc_first_name is None or cc_last_name is None or cc_nic is None:
                  ${accomplishment_copy_name | h,uppercase}${accomplishment_copy_description_full}${accomplishment_copy_course_name}${accomplishment_copy_course_description}
                % else:
                  ${cc_first_name | h } ${cc_last_name | h} com Cartão Cidadão número
                  % if cc_nic_check_digit is None: 
                    ${cc_nic | h}${accomplishment_copy_description_full}${accomplishment_copy_course_name}${accomplishment_copy_course_description}
                  % else: 
                    ${cc_nic | h} ${cc_nic_check_digit | h}${accomplishment_copy_description_full}${accomplishment_copy_course_name}${accomplishment_copy_course_description}
                  % endif
                % endif
              </p>
              <p class="cert-text right">Lisboa, ${certificate_date_issued}</p>
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
                        % if signatory['name'] <> "":
                      <div class="ednxt-certificate__footer-signatory">
                         % if signatory['signature_image_path'] <> "":
                           <img class="ednxt-certificate__footer-signatory_signature" src="${static.url(signatory['signature_image_path'])}" alt="${signatory['name']}">
                         % endif
                        <p class="ednxt-certificate__footer-signatory_credentials">
                          <span class="signatory">(${signatory['name']})</span><br/>
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
              % if not context.get('certificate_background') or force_add_course_image_left_panel:
                <img class="course-image" src="${full_course_image_url}" alt="Imagem do curso">
              % endif

              % if not context.get('certificate_background') or force_add_course_name_left_panel:
              <div class="left-panel-course-name">
                ${accomplishment_copy_course_name}
              </div>
              % endif

              % if (not context.get('certificate_background') or force_add_organization_logo_to_header ) and organization_logo_url:
                <img class="organization-logo" src="${organization_logo_url}" alt="${organization_long_name}">
              % endif
              
              % if context.get('footer_additional_logo'):
                <img class="footer-additional-logo" src="${footer_additional_logo}">
              % endif

              <img class="nau-logo-funders" src="${static.certificate_asset_url('3logos-financiadores-portugal-2020-compete-feder')}" alt="Logos das entidades financiadoras">
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
          ## Replace http://localhost:5000 with //${ request.get_host().replace('lms','course-certificate') }
          window.location.assign("//${ request.get_host().replace('lms','course-certificate') }/attachment${request.META.get('RAW_URI')}");
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
