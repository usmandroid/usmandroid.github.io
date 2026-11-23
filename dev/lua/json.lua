-- Minimal JSON decoder (no dependencies, so it works without lualibs / texlive-luatex).
-- json.decode(text) -> Lua value. Arrays are 1..n tables, objects are string-keyed tables.
local json = {}

local escapes =
  { ['"'] = '"', ["\\"] = "\\", ["/"] = "/", b = "\b", f = "\f", n = "\n", r = "\r", t = "\t" }

local function skip(s, i)
  return s:find("[^ \t\r\n]", i) or #s + 1
end

local parse_value

local function parse_string(s, i)
  local out, j = {}, i + 1
  while true do
    local c = s:sub(j, j)
    if c == "" then
      error("json: unterminated string")
    end
    if c == '"' then
      return table.concat(out), j + 1
    end
    if c == "\\" then
      local e = s:sub(j + 1, j + 1)
      if e == "u" then
        local cp = tonumber(s:sub(j + 2, j + 5), 16)
        j = j + 6
        if cp >= 0xD800 and cp < 0xDC00 and s:sub(j, j + 1) == "\\u" then
          local lo = tonumber(s:sub(j + 2, j + 5), 16)
          cp = 0x10000 + (cp - 0xD800) * 0x400 + (lo - 0xDC00)
          j = j + 6
        end
        out[#out + 1] = utf8.char(cp)
      else
        out[#out + 1] = escapes[e] or error("json: bad escape \\" .. e)
        j = j + 2
      end
    else
      local k = s:find('["\\]', j) or #s + 1
      out[#out + 1] = s:sub(j, k - 1)
      j = k
    end
  end
end

local function parse_array(s, i)
  local arr, n = {}, 0
  i = skip(s, i + 1)
  if s:sub(i, i) == "]" then
    return arr, i + 1
  end
  while true do
    local v
    v, i = parse_value(s, i)
    n = n + 1
    arr[n] = v
    i = skip(s, i)
    local c = s:sub(i, i)
    if c == "]" then
      return arr, i + 1
    end
    if c ~= "," then
      error("json: expected , or ] at " .. i)
    end
    i = i + 1
  end
end

local function parse_object(s, i)
  local obj = {}
  i = skip(s, i + 1)
  if s:sub(i, i) == "}" then
    return obj, i + 1
  end
  while true do
    i = skip(s, i)
    if s:sub(i, i) ~= '"' then
      error("json: expected string key at " .. i)
    end
    local k
    k, i = parse_string(s, i)
    i = skip(s, i)
    if s:sub(i, i) ~= ":" then
      error("json: expected : at " .. i)
    end
    local v
    v, i = parse_value(s, i + 1)
    obj[k] = v
    i = skip(s, i)
    local c = s:sub(i, i)
    if c == "}" then
      return obj, i + 1
    end
    if c ~= "," then
      error("json: expected , or } at " .. i)
    end
    i = i + 1
  end
end

function parse_value(s, i)
  i = skip(s, i)
  local c = s:sub(i, i)
  if c == "{" then
    return parse_object(s, i)
  end
  if c == "[" then
    return parse_array(s, i)
  end
  if c == '"' then
    return parse_string(s, i)
  end
  if s:sub(i, i + 3) == "true" then
    return true, i + 4
  end
  if s:sub(i, i + 4) == "false" then
    return false, i + 5
  end
  if s:sub(i, i + 3) == "null" then
    return nil, i + 4
  end
  local num = s:match("^-?%d+%.?%d*[eE]?[+-]?%d*", i)
  if num and #num > 0 then
    return tonumber(num), i + #num
  end
  error("json: unexpected character '" .. c .. "' at " .. i)
end

function json.decode(s)
  local v, i = parse_value(s, 1)
  i = skip(s, i)
  if i <= #s then
    error("json: trailing data at " .. i)
  end
  return v
end

return json
