-- `make doctor`: the pure-Lua JSON reader parses every data file
local json = dofile("dev/lua/json.lua")
assert(json.decode('{"a":[1,2,"\\u00e4"]}').a[2] == 2)
for _, f in ipairs({ "personal", "edu", "exp", "proj", "pubs" }) do
  local fh = assert(io.open("_data/" .. f .. ".json", "r"))
  assert(json.decode(fh:read("*a")), f)
  fh:close()
end
print("ok       dev/lua/json.lua reads _data/*.json")
