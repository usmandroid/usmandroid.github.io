-- Prints the _data/*.json files as LaTeX macros (see main.tex, publications.tex).
-- Run from the repository root (the Makefile does): paths are relative to it.
local json = dofile("dev/lua/json.lua")

local function read_json(file)
  local fh = assert(io.open(file, "r"))
  local s = fh:read("*a")
  fh:close()
  return json.decode(s)
end

-- Escape TeX specials and turn non-ASCII characters into T1-safe macros, so the document
-- compiles with plain Type1 fonts (no fontspec / luaotfload / texlive-luatex needed).
local specials = {
  ["\\"] = "\\textbackslash{}",
  ["{"] = "\\{",
  ["}"] = "\\}",
  ["&"] = "\\&",
  ["%"] = "\\%",
  ["$"] = "\\$",
  ["#"] = "\\#",
  ["_"] = "\\_",
  ["^"] = "\\^{}",
  ["~"] = "\\~{}",
}
local unicode = {
  [0x00E4] = '\\"a',
  [0x00F6] = '\\"o',
  [0x00FC] = '\\"u',
  [0x00C4] = '\\"A',
  [0x00D6] = '\\"O',
  [0x00DC] = '\\"U',
  [0x00DF] = "\\ss{}",
  [0x00E9] = "\\'e",
  [0x00E8] = "\\`e",
  [0x00EA] = "\\^e",
  [0x00EB] = '\\"e',
  [0x00C9] = "\\'E",
  [0x00E1] = "\\'a",
  [0x00E0] = "\\`a",
  [0x00E2] = "\\^a",
  [0x00ED] = "\\'i",
  [0x00F3] = "\\'o",
  [0x00FA] = "\\'u",
  [0x00F1] = "\\~n",
  [0x00E7] = "\\c{c}",
  [0x00E5] = "\\aa{}",
  [0x00F8] = "\\o{}",
  [0x0142] = "\\l{}",
  [0x010D] = "\\v{c}",
  [0x010C] = "\\v{C}",
  [0x0161] = "\\v{s}",
  [0x0160] = "\\v{S}",
  [0x017E] = "\\v{z}",
  [0x017D] = "\\v{Z}",
  [0x0159] = "\\v{r}",
  [0x011B] = "\\v{e}",
  [0x2013] = "--",
  [0x2014] = "---",
  [0x2018] = "`",
  [0x2019] = "'",
  [0x201C] = "``",
  [0x201D] = "''",
  [0x2026] = "\\ldots{}",
  [0x00B7] = "\\textperiodcentered{}",
  [0x00D7] = "$\\times$",
  [0x00B0] = "\\textdegree{}",
  [0x00A0] = "~",
}
local function esc(s)
  local parts = {}
  for _, c in utf8.codes(tostring(s or "")) do
    if c < 128 then
      local ch = string.char(c)
      parts[#parts + 1] = specials[ch] or ch
    elseif unicode[c] then
      parts[#parts + 1] = unicode[c]
    else
      texio.write_nl(
        "parser.lua: unsupported character U+" .. string.format("%04X", c) .. ", replaced by ?"
      )
      parts[#parts + 1] = "?"
    end
  end
  return table.concat(parts)
end

local function out(s)
  tex.print(s)
end

-- Language/technology tags: personal.json "options" {show_languages, languages_as_list},
-- overridable with the environment variables RESUME_LANGS=0|1 and RESUME_LANGS_LIST=0|1.
local function env_flag(name, default)
  local v = os.getenv(name)
  if v == nil or v == "" then
    return default
  end
  return v == "1" or v == "true" or v == "yes"
end
local flags
local function max_chars() -- strict line limit for lists (skills, Tech lines, languages); RESUME_MAX_CHARS overrides
  local o = read_json("_data/personal.json")[1].options or {}
  return tonumber(os.getenv("RESUME_MAX_CHARS")) or o.max_line_chars or 90
end
-- greedy wrap of items into lines of at most `limit` characters (prefix counts on the first line,
-- `indent` on the others); an item longer than the limit stays alone on its line
local function wrap_items(prefix_len, items, sep_len, limit, indent)
  local trail = 1 -- the "," kept at the end of a wrapped line
  local lines, cur, len = {}, {}, prefix_len
  for _, it in ipairs(items) do
    local n = utf8.len(it)
    local add = (#cur == 0) and n or (sep_len + n)
    if #cur > 0 and len + add + trail > limit then
      lines[#lines + 1] = cur
      cur, len = { it }, indent + n
    else
      cur[#cur + 1] = it
      len = len + add
    end
  end
  lines[#lines + 1] = cur
  return lines
end
local function esc_join(items, sep)
  local e = {}
  for i, it in ipairs(items) do
    e[i] = esc(it)
  end
  return table.concat(e, sep)
end
local function lang_flags()
  if not flags then
    local o = read_json("_data/personal.json")[1].options or {}
    flags = {
      show = env_flag("RESUME_LANGS", o.show_languages ~= false),
      list = env_flag("RESUME_LANGS_LIST", o.languages_as_list == true),
    }
  end
  return flags
end
-- -> tags for the heading line, extra line appended to the description
local function lang_parts(tags)
  local f, items = lang_flags(), {}
  for w in tostring(tags or ""):gmatch("%S+") do
    items[#items + 1] = w
  end
  if not f.show or #items == 0 then
    return "", ""
  end
  if f.list then
    local lines, parts = wrap_items(#"Tech: ", items, 2, max_chars(), 2), {}
    for i, l in ipairs(lines) do
      parts[i] = ((i == 1) and "Tech: " or "\\hspace*{1.2em}")
        .. esc_join(l, ", ")
        .. ((i < #lines) and "," or "")
    end
    return "",
      "\\newline{\\scriptsize\\textcolor{light-gray}{" .. table.concat(parts, "\\newline ") .. "}}"
  end
  return esc_join(items, " "), ""
end

function printEduItems(file)
  for _, e in ipairs(read_json(file)) do
    out(
      "\\resumeEduEntry{"
        .. esc(e.school)
        .. "}{"
        .. esc(e.school_location)
        .. "}{"
        .. esc(e.degree)
        .. "}{"
        .. esc(e.time_period)
        .. "}"
    )
    if e.details then
      out("\\resumeItemListStart")
      for _, d in ipairs(e.details) do
        out("\\resumePlainItem{" .. esc(d) .. "}")
      end
      out("\\resumeItemListEnd")
    end
  end
end

function printExpItems(file)
  for _, e in ipairs(read_json(file)) do
    out(
      "\\resumeExpEntry{"
        .. esc(e.company)
        .. "}{"
        .. esc(e.company_location)
        .. "}{"
        .. esc(e.role)
        .. "}{"
        .. esc(e.team)
        .. "}{"
        .. esc(e.time_duration)
        .. "}"
    )
    out("\\resumeItemListStart")
    for _, d in ipairs(e.details or {}) do
      local tags, extra = lang_parts(d.languages)
      out(
        "\\resumeItem{"
          .. esc(d.title)
          .. "}{"
          .. esc(d.description)
          .. extra
          .. "}{"
          .. tags
          .. "}"
      )
    end
    out("\\resumeItemListEnd")
  end
end

function printProjItems(file)
  for _, p in ipairs(read_json(file)) do
    local tags, extra = lang_parts(p.languages)
    out(
      "\\resumeSubItem{"
        .. esc(p.title)
        .. "}{"
        .. esc(p.description)
        .. extra
        .. "}{"
        .. tags
        .. "}"
    )
  end
end

-- authors with the owner's name in bold
local function authors_tex(authors, me)
  local list = {}
  for _, a in ipairs(authors) do
    list[#list + 1] = (a == me) and ("\\textbf{" .. esc(a) .. "}") or esc(a)
  end
  return table.concat(list, ", ")
end

local function nonempty(v)
  return v ~= nil and v ~= ""
end

-- "Venue, place, pages. DOI: x. Links: Paper, PDF. Note." with the venue in italics.
-- Empty doi / link urls are placeholders and are skipped.
local function venue_tex(p, with_links)
  local s = "\\textit{" .. esc(p.venue) .. "}"
  if nonempty(p.place) then
    s = s .. ", " .. esc(p.place)
  end
  if nonempty(p.pages) then
    s = s .. ", " .. esc(p.pages)
  end
  s = s .. "."
  if nonempty(p.doi) then
    s = s .. " DOI: \\href{https://doi.org/" .. p.doi .. "}{" .. esc(p.doi) .. "}."
  end
  if with_links then
    local ls = {}
    for _, l in ipairs(p.links or {}) do
      if nonempty(l.url) then
        ls[#ls + 1] = "\\href{" .. l.url .. "}{" .. esc(l.label) .. "}"
      end
    end
    if #ls > 0 then
      s = s .. " Links: " .. table.concat(ls, ", ") .. "."
    end
  end
  if nonempty(p.note) then
    s = s .. " " .. esc(p.note) .. "."
  end
  return s
end

-- abstracts: personal.json options.show_abstract, or RESUME_ABSTRACT=0|1
local function show_abstract()
  local o = read_json("_data/personal.json")[1].options or {}
  return env_flag("RESUME_ABSTRACT", o.show_abstract == true)
end

-- compact list for the resume: authors, bold title, venue
function printPubItems(file, personal_file)
  local me = read_json(personal_file)[1].name
  for _, p in ipairs(read_json(file)) do
    out(
      "\\resumePubItem{"
        .. authors_tex(p.authors, me)
        .. "}{"
        .. esc(p.title)
        .. "}{"
        .. venue_tex(p)
        .. "}"
    )
  end
end

-- full list for publications.tex: numbered, with abstract and keywords
function printPubFull(file, personal_file)
  local me = read_json(personal_file)[1].name
  local show = show_abstract()
  for i, p in ipairs(read_json(file)) do
    out(
      "\\pubEntry{"
        .. i
        .. "}{"
        .. esc(p.title)
        .. "}{"
        .. authors_tex(p.authors, me)
        .. "}{"
        .. venue_tex(p, true)
        .. "}"
    )
    if show and nonempty(p.abstract) then
      local kw = p.keywords and table.concat(p.keywords, "; ") or ""
      out("\\pubAbstract{" .. esc(p.abstract) .. "}{" .. esc(kw) .. "}")
    end
  end
end

function printHeading(file)
  local p = read_json(file)[1]
  out("\\begin{tabular*}{\\textwidth}{l@{\\extracolsep{\\fill}}r}")
  out(
    "\\textbf{\\href{"
      .. p.website
      .. "/}{\\Large "
      .. esc(p.name)
      .. "}} & Email: \\href{mailto:"
      .. p.email
      .. "}{"
      .. esc(p.email)
      .. "}\\\\"
  )
  out(
    "\\href{"
      .. p.website
      .. "/}{"
      .. esc(p.website)
      .. "} & \\href{"
      .. p.github
      .. "}{GitHub} $\\cdot$ \\href{"
      .. p.linkedin
      .. "}{LinkedIn}\\\\"
  )
  -- phone and address only when personal.json has them AND sets "show_private_contact": true
  if p.show_private_contact then
    if p.phone then
      out(" & Phone: " .. esc(p.phone) .. "\\\\")
    end
    if p.address then
      out(" & Address: " .. esc(p.address) .. "\\\\")
    end
  end
  out("\\end{tabular*}")
end

function printList(file, primary, secondary)
  local parts = {}
  for _, v in ipairs(read_json(file)[1][primary]) do
    parts[#parts + 1] = esc(v[secondary])
  end
  out(table.concat(parts, ", "))
end

-- skill_groups: [{label, items:[...]}] as one plain item each
function printSkillGroups(file)
  for _, g in ipairs(read_json(file)[1].skill_groups or {}) do
    local lines, parts = wrap_items(utf8.len(g.label) + 2, g.items, 2, max_chars(), 2), {}
    for i, l in ipairs(lines) do
      parts[i] = ((i == 1) and ("\\textbf{" .. esc(g.label) .. "}: ") or "\\hspace*{1.2em}")
        .. esc_join(l, ", ")
        .. ((i < #lines) and "," or "")
    end
    out("\\resumePlainItem{" .. table.concat(parts, "\\newline ") .. "}")
  end
end

function printCertItems(file)
  for _, c in ipairs(read_json(file)[1].certificates or {}) do
    out("\\resumePlainItem{" .. esc(c) .. "}")
  end
end

function printSpoken(file)
  local lines, parts =
    wrap_items(0, read_json(file)[1].spoken_languages or {}, 2, max_chars(), 0), {}
  for i, l in ipairs(lines) do
    parts[i] = esc_join(l, ", ") .. ((i < #lines) and "," or "")
  end
  out(table.concat(parts, "\\newline "))
end

function printOwnerName(file)
  out(esc(read_json(file)[1].name))
end
