function initGraph(graphName)

    local http = require('microhttp')

    local URL_PREFIX = "http://localhost:5000/api/"
    local CHUNK_SIZE = 4096

    local graphCount
    local graphs = {}

    local colors = {
        RGB(0, 192, 192),
        RGB(192, 0, 192),
        RGB(192, 192, 0),
        RGB(96, 192, 0),
        RGB(0, 96, 192),
        RGB(192, 0, 96),
        RGB(192, 96, 0),
        RGB(0, 192, 96),
        RGB(96, 0, 192),
        RGB(192, 192, 192)
    }

    os.setlocale("en_US.UTF-8")

    local response, status = http.request(URL_PREFIX .. "graphs/" .. graphName .. "/descrs")
    assert(status >= 200 and status < 300, response)

    graphCount = 0
    for name, title, lineType in string.gmatch(response .. "\n", " *(.-) *; *(.-) *; *(.-) *\n") do
        if title == "" then
            title = name
        end
        if name ~= "" and name ~= title then
            title = title .. " (" .. name .. ")"
        end
        table.insert(graphs, {
            Name  = title,
            Color = colors[graphCount % 10 + 1],
            Type  = tonumber(lineType) or 1,
            Width = 1
        })
        graphCount = graphCount + 1
    end

    local response, status = http.request(URL_PREFIX .. "graphs/" .. graphName .. "/params")
    assert(status >= 200 and status < 300, response)

    for param, value in string.gmatch(response .. "\n", " *(.-) *= *(.-) *\n") do
        assert(param ~= "Name" and param ~= "line", "Illegal parameter name (" .. param .. ")")
        Settings[param] = value
    end

    local builderId = nil
    local priorIndex = nil

    local graphValues
    local valueOffset
    local valueCount

    local calcOk

    return graphCount, graphs, function(index)

        local isInitIndex = (priorIndex == nil or index < priorIndex)
        priorIndex = index

        if isInitIndex then
            calcOk = true
        elseif not calcOk then
            return nil
        end

        local retValues = {}

        local msg
        calcOk, msg = pcall(function()
            if builderId == nil then
                local attrs = {}
                info = getDataSourceInfo()
                table.insert(attrs, info.interval)
                table.insert(attrs, info.class_code)
                table.insert(attrs, info.sec_code)

                local response, status = http.request(
                    URL_PREFIX .. "graphs/" .. graphName .. "/new",
                    table.concat(attrs, "\n")
                )
                assert(status >= 200 and status < 300, response)
                builderId = response
            end

            if isInitIndex then
                local params = {}
                for param, value in pairs(Settings) do
                    if param ~= "Name" and param ~= "line" then
                        table.insert(params, param .. "=" .. value)
                    end
                end

                local response, status = http.request(
                    URL_PREFIX .. "graphs/" .. builderId .. "/params",
                    table.concat(params, "\n")
                )
                assert(status >= 200 and status < 300, response)
            end

            if isInitIndex or index > (valueOffset + valueCount - 1) then
                --TODO: Leverage the CandleExist function

                graphValues = {}
                valueOffset = index
                valueCount = math.min(CHUNK_SIZE, Size() - index + 1)

                local price = {}
                local volume = {}
                local time = {}
                for i = index, (index + valueCount - 1) do
                    local c = C(i)
                    table.insert(price, (c and tostring(c) or ""))

                    local v = V(i)
                    table.insert(volume, (v and tostring(v) or ""))

                    local t = T(i)
                    table.insert(time, (t and string.format(
                        "%04d-%02d-%02dT%02d:%02d:%02d.%03d",
                        t.year, t.month, t.day, t.hour, t.min, t.sec, t.ms
                    ) or ""))
                end

                local response, status = http.request(
                    URL_PREFIX .. "graphs/" .. builderId .. "/values",
                    table.concat(price, ";") .. "\n" .. table.concat(volume, ";") .. "\n" .. table.concat(time, ";")
                )
                assert(status >= 200 and status < 300, response)

                local graphIndex = 1
                for line in string.gmatch(response .. "\n", "(.-)\n") do
                    if graphIndex > graphCount then break end
                    local values = {}
                    local count = 0
                    for value in string.gmatch(line .. ";", "(.-);") do
                        count = count + 1
                        values[count] = tonumber(value) -- table.insert() will corrupt the data with nils
                    end
                    if count > 0 then
                        local offset = values[1] or 0
                        values[1] = nil
                        assert(offset <= 0 and valueOffset + offset >= 1, "Invalid data chunk offset (" .. offset .. ")")
                        for i = offset, -1 do
                            SetValue(valueOffset + i, graphIndex, values[2 - offset + i])
                        end
                        table.move(values,
                            2 - offset,
                            math.max(count, 2 - offset + count - 1),
                            1)
                    end
                    table.insert(graphValues, values)
                    graphIndex = graphIndex + 1
                end
            end

            local valueIndex = index - valueOffset + 1
            if valueIndex >= 1 and valueIndex <= valueCount then
                for i, values in ipairs(graphValues) do
                    retValues[i] = values[valueIndex]
                end
            end
        end)
        assert(calcOk, msg)

        return table.unpack(retValues, 1, graphCount)
    end
end
