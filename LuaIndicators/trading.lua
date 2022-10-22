dofile(getWorkingFolder() .. "\\LuaIndicators\\lib\\microtrader.lua")

local GRAPH_NAME = "trading"

Settings = {
    Name = "MicroTrader: " .. (GRAPH_TITLE or GRAPH_NAME)
}

local calcFunc

function Init()

    graphCount, Settings.line, calcFunc = initGraph(GRAPH_NAME)
    return graphCount

end

function OnCalculate(index)

    return calcFunc(index)

end
