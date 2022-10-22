#include <string>
#include <vector>
#include "curlext.h"
#include "HttpHeader.h"

#define LUA_LIB
#define LUA_BUILD_AS_DLL
#include "lua.hpp"

int getTimeout(lua_State *luaState);
int setTimeout(lua_State *luaState);
int getHeaders(lua_State *luaState);
int setHeaders(lua_State *luaState);
int request(lua_State *luaState);

size_t writeResponseHeader(void *ptr, size_t size, size_t nmemb, HttpHeaders *data);
size_t writeResponseBody(void *ptr, size_t size, size_t nmemb, std::string *data);
HttpHeaders getHeadersFromTable(lua_State *luaState, int tableIndex);
void createHeaderTable(lua_State *luaState, const HttpHeaders &headers);

struct ApiContext
{
    CurlGlobal curlGlobal;

    long timeout = 30L;
    HttpHeaders headers;
};

ApiContext apiContext;

extern "C" LUALIB_API int luaopen_microhttp(lua_State *luaState)
{
    static const luaL_Reg api[] = {
        {"getTimeout", getTimeout},
        {"setTimeout", setTimeout},
        {"getHeaders", getHeaders},
        {"setHeaders", setHeaders},
        {"request", request},
        {nullptr}
    };

    luaL_newlib(luaState, api);
    return 1;
}

int getTimeout(lua_State *luaState)
{
    lua_pushinteger(luaState, apiContext.timeout);
    return 1;
}

int setTimeout(lua_State *luaState)
{
    long timeout = luaL_checkinteger(luaState, 1);
    if(timeout < 0L) luaL_error(luaState, "Invalid timeout value: %d", int(timeout));
    
    apiContext.timeout = timeout;
    return 0;
}

int getHeaders(lua_State *luaState)
{
    createHeaderTable(luaState, apiContext.headers);
    return 1;
}

int setHeaders(lua_State *luaState)
{
    luaL_checktype(luaState, 1, LUA_TTABLE);
    apiContext.headers = getHeadersFromTable(luaState, 1);
    return 0;
}

int request(lua_State *luaState)
{
    const char *url = luaL_checkstring(luaState, 1);
    const char *requestBody = luaL_optstring(luaState, 2, nullptr);
    const char *requestMethod = luaL_optstring(luaState, 3, nullptr);
    if(!lua_isnoneornil(luaState, 4)) luaL_checktype(luaState, 4, LUA_TTABLE);

    try {
        CurlEasyPtr curl = apiContext.curlGlobal.easyInit();
        if(!curl) {
            throw std::runtime_error("Can't initialize curl library");
        }

        CurlSlist requestHeaders;

        auto addHeader = [&requestHeaders](const HttpHeader &header) {
            if(!requestHeaders.add(header.getString().c_str())) {
                throw std::runtime_error("Can't prepare HTTP headers with curl");
            }
        };

        if(requestBody) {
            addHeader(HttpHeader("Content-Type", "text/plain"));
        }
        for(const HttpHeader &header: apiContext.headers) {
            addHeader(header);
        }
        if(!lua_isnoneornil(luaState, 4)) {
            for(const HttpHeader &header: getHeadersFromTable(luaState, 4)) {
                addHeader(header);
            }
        }

        long responseCode = 0;
        HttpHeaders responseHeaders;
        std::string responseBody;

        CurlExec curlExec;
        char curlErrorMsg[CURL_ERROR_SIZE] = {0};

        if(!curlExec(curl_easy_setopt(curl.get(), CURLOPT_ERRORBUFFER, curlErrorMsg)) ||
            !curlExec(curl_easy_setopt(curl.get(), CURLOPT_TIMEOUT, apiContext.timeout)) ||
            !curlExec(curl_easy_setopt(curl.get(), CURLOPT_URL, url)) ||
            (requestMethod && !curlExec(curl_easy_setopt(curl.get(), CURLOPT_CUSTOMREQUEST, requestMethod))) ||
            (requestHeaders && !curlExec(curl_easy_setopt(curl.get(), CURLOPT_HTTPHEADER, requestHeaders.get()))) ||
            (requestBody && !curlExec(curl_easy_setopt(curl.get(), CURLOPT_POSTFIELDS, requestBody))) ||
            !curlExec(curl_easy_setopt(curl.get(), CURLOPT_HEADERFUNCTION, writeResponseHeader)) ||
            !curlExec(curl_easy_setopt(curl.get(), CURLOPT_HEADERDATA, &responseHeaders)) ||
            !curlExec(curl_easy_setopt(curl.get(), CURLOPT_WRITEFUNCTION, writeResponseBody)) ||
            !curlExec(curl_easy_setopt(curl.get(), CURLOPT_WRITEDATA, &responseBody)) ||
            !curlExec(curl_easy_perform(curl.get())) ||
            !curlExec(curl_easy_getinfo(curl.get(), CURLINFO_RESPONSE_CODE, &responseCode)))
        {
            throw std::runtime_error(curlErrorMsg[0] ? curlErrorMsg : curl_easy_strerror(curlExec.getResult()));
        }

        lua_pushstring(luaState, responseBody.c_str());
        lua_pushinteger(luaState, responseCode);
        createHeaderTable(luaState, responseHeaders);
        return 3;
    }
    catch(const std::exception &e) {
        return luaL_error(luaState, e.what());
    }
}

size_t writeResponseHeader(void *ptr, size_t size, size_t nmemb, HttpHeaders *data)
{
    std::string header(static_cast<char*>(ptr), size * nmemb);
    int pos = header.find(':');
    if(pos != std::string::npos) {
        std::string key = header.substr(0, pos - 1);
        std::string value = header.substr(header.find_first_not_of(' ', pos + 1));
        data->push_back(HttpHeader(key, value));
    }
    return size * nmemb;
}

size_t writeResponseBody(void *ptr, size_t size, size_t nmemb, std::string *data)
{
    data->append(static_cast<char *>(ptr), size * nmemb);
    return size * nmemb;
}

HttpHeaders getHeadersFromTable(lua_State *luaState, int tableIndex)
{
    HttpHeaders headers;

    lua_pushnil(luaState);
    while(lua_next(luaState, tableIndex) != 0) {
        const char *value = lua_tostring(luaState, -1);
        if(!value) luaL_error(luaState, "Header value must be of string type");
        lua_pop(luaState, 1);

        lua_pushvalue(luaState, -1);
        const char *key = lua_tostring(luaState, -1);
        if(!key) luaL_error(luaState, "Header key must be of string type");
        lua_pop(luaState, 1);

        headers.push_back(HttpHeader(key, value));
    }
    return headers;
}

void createHeaderTable(lua_State *luaState, const HttpHeaders &headers)
{
    lua_createtable(luaState, 0, headers.size());
    for(const HttpHeader &header: headers) {
        lua_pushstring(luaState, header.getKey().c_str());
        lua_pushstring(luaState, header.getValue().c_str());
        lua_settable(luaState, -3);
    }
}
