from flask import Flask, request
from werkzeug.exceptions import HTTPException, NotFound
from datetime import datetime
from uuid import UUID
import logging

from lib.exceptions import ParamError
from lib.cache import Cache

from graphs.graphs import *
from graphs.sandbox import SandboxGraphConfig
from graphs.trading import TradingGraphConfig

from trading.orders import Orders

app = Flask(__name__)

URL_PREFIX = "/api/"
APP_LOG_LEVEL = logging.ERROR
GRAPH_BUILDER_LIMIT = 64

graphConfigs = {
    graphConfig.getName(): graphConfig
    for graphConfig in GraphConfig.__subclasses__()
}

graphBuilders = Cache(GRAPH_BUILDER_LIMIT)

def getGraphConfig(name):
    try:
        return graphConfigs[name]
    except Exception as e:
        raise NotFound(f"Invalid graph builder name: {e}")

def getGraphBuilder(id):
    try:
        return graphBuilders[UUID(id)]
    except Exception as e:
        raise NotFound(f"Invalid graph builder id: {e}")

@app.route(URL_PREFIX + "graphs/<name>/descrs", methods=["GET"])
def getGraphDescrs(name):
    return "\n".join(
        ";".join([
            graphDescr["name"], 
            graphDescr.get("title", ""), 
            str(graphDescr.get("lineType", 1))
        ])
        for graphDescr in getGraphConfig(name).getGraphDescrs()
    )

@app.route(URL_PREFIX + "graphs/<name>/params", methods=["GET"])
def getGraphParams(name):
    return "\n".join(
        f"{paramName}={paramValue}" 
        for paramName, paramValue in getGraphConfig(name).getDefaultParams().items()
    )

@app.route(URL_PREFIX + "graphs/<name>/new", methods=["POST"])
def getGraphNew(name):
    try:
        attrs = request.data.decode("utf-8").split("\n")
        interval = int(attrs[0])
        classCode = attrs[1]
        secCode = attrs[2]
    except Exception:
        return "Invalid attribute(s)", 400

    return str(graphBuilders.add(
        GraphBuilder(interval, classCode, secCode, getGraphConfig(name))
    ))

@app.route(URL_PREFIX + "graphs/<id>/params", methods=["POST"])
def postGraphParams(id):
    params = {
        paramName.strip(): paramValue
        for paramName, s, paramValue in (
            line.partition("=")
            for line in request.data.decode("utf-8").split("\n")
        )
        if s
    }

    graphBuilders[UUID(id)] = getGraphBuilder(id).copyWithParams(params)

    return ""

@app.route(URL_PREFIX + "graphs/<id>/values", methods=["POST"])
def postGraphValues(id):
    try:
        values = request.data.decode("utf-8").split("\n")
        price = [
            float(value)
            if value.strip() else None
            for value in values[0].split(";")
        ]
        volume = [
            float(value)
            if value.strip() else None
            for value in values[1].split(";")
        ]
        time = [
            datetime.fromisoformat(value)
            if value.strip() else None
            for value in values[2].split(";")
        ]
    except Exception:
        return "Invalid value(s)", 400

    return "\n".join(
        "" if values is None
        else ";".join(
                "" if value is None
                else str(value)
                for value in values
            )
        for values in getGraphBuilder(id).calcValues(price, volume, time)
    )

@app.route(URL_PREFIX + "orders", methods=["GET"])
def getOrders():
    return "\n\n".join(
        "\n".join(
            f"{paramName}={paramValue}"        
            for paramName, paramValue in order.items()
        )
        for order in Orders.getNew()
    )

@app.errorhandler(ParamError)
def paramError(e):
    return str(e), 400

@app.errorhandler(HTTPException)
def httpException(e):
    return str(e), e.code

if __name__ == "__main__":
    log = logging.getLogger("werkzeug")
    log.setLevel(APP_LOG_LEVEL)

    app.run(debug = False)
