-- reveal-header.lua — publish config to <meta> for the JS plugin

local function S(v)
  if not v then return "" end
  return pandoc.utils.stringify(v)
end

function Meta(m)
  if quarto and quarto.doc and quarto.doc.add_html_dependency then
    local prefer_slide_header = m["prefer-slide-header"]
    local prefer_slide_header_str = tostring(not (prefer_slide_header == false)) -- default TRUE

    local skip_title_lift = m["skip-title-lift"]
    local skip_title_lift_str = tostring(skip_title_lift == true)                -- default FALSE

    quarto.doc.add_html_dependency({
      name = "reveal-header",
      scripts = {"reveal-header.js"},
      stylesheets = {"reveal-header.css"},
      meta = {
        ["reveal-header-default"]              = S(m["header"]),
        ["reveal-header-logo"]                 = S(m["header-logo"]),
        ["reveal-header-logo-link"]            = S(m["header-logo-link"]),
        ["reveal-header-footer-logo-link"]     = S(m["footer-logo-link"]),
        ["reveal-header-home-link"]            = S(m["header-home-link"]),
        ["reveal-header-home-text"]            = S(m["header-home-text"]),
        ["reveal-header-title-as-default"]     = tostring(m["title-as-header"] == true),
        ["reveal-header-subtitle-as-default"]  = tostring(m["subtitle-as-header"] == true),
        ["reveal-header-hide-from-titleslide"] = S(m["hide-from-titleSlide"]),

        -- Behavior toggles:
        ["reveal-header-prefer-slide-header"]  = prefer_slide_header_str,
        ["reveal-header-skip-title-lift"]      = skip_title_lift_str,

        -- Title slide explicit override text
        ["reveal-header-title-slide-header"]   = S(m["title-slide-header"])
      }
    })
  end
  return m
end
