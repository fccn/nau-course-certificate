<%! from django.utils.translation import ugettext as _ %>
<%! from django.utils.translation import activate%>
<%
  activate(user_language)
%>
<%namespace name='static' file='/static_content.html'/>
<%
# set doc language direction
from django.utils.translation import get_language_bidi
dir_rtl = 'rtl' if get_language_bidi() else 'ltr'
course_mode_class = course_mode if course_mode else ''

nau_certificate_issued_display_iframe = True
%>
<!DOCTYPE html>
<html class="no-js" lang="${user_language}">
<head dir="${dir_rtl}">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  ## metas for pdf printing
  <meta name="pdfkit-page-size" content="A4">
  <meta name="pdfkit-orientation" content="Landscape">
  
  ## Fix put certificate on middle of the page
  <meta name="pdfkit-margin-left" content="0mm" />
  <meta name="pdfkit-margin-right" content="0mm" />
  <meta name="pdfkit-margin-bottom" content="0mm" />
  <meta name="pdfkit-margin-top" content="0mm" />
  <meta name="pdfkit-zoom" content="2" />

  <meta name="nau-course-certificate-version" content="certificate_template_version_2020_11_16_3_certificate_date_${certificate_date_issued}">
  <meta name="nau-course-certificate-filename" content="certificado-nau-curso-${course_id}.pdf">
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

.ednxt-certificate__footer-information {
    position: absolute;
    left: -1cm;
    bottom: 0.8cm;
    z-index: 1;
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

.nau-logo-funders
{
    max-width: 9cm !important;
    position: absolute;
    left: 10cm;
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

.ednxt-certificate__footer-information_id a {
    color: #a7a4a4;
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
  max-height: 1.5cm;
  position: absolute;
  left: 10cm;
  top: 1.2cm;
  max-width: 12cm;
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
                def title_case(in_str):
                  return ' '.join(w.title() if len(w) > 2 else w.lower() for w in in_str.split()) if in_str else None
                %>
                ${certificate_description}
                % if cc_first_name is None or cc_last_name is None or cc_nic is None:
                  <span class="cert-text name">${accomplishment_copy_name | h}</span>,
                % else:
                  <span class="cert-text name">${cc_first_name | title_case } ${cc_last_name | title_case}</span> com Cartão Cidadão número
                  % if cc_nic_check_digit is None: 
                    ${cc_nic},
                  % else: 
                    ${cc_nic} ${cc_nic_check_digit},
                  % endif
                % endif
                ${accomplishment_copy_description_full} ${accomplishment_copy_course_name} ${accomplishment_copy_course_description}
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

              % if not context.get('certificate_background') or force_add_organization_logo_to_header:
              <img class="organization-logo" src="https://uploads.static.stage.nau.fccn.pt/${organization_logo}" alt="${organization_long_name}">
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