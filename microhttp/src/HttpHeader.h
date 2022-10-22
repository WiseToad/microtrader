#ifndef HTTP_HEADER_H
#define HTTP_HEADER_H

#include <string>
#include <vector>

struct HttpHeader
{
    HttpHeader(const std::string &key, const std::string &value):
        key(key), value(value)
    {}

    std::string getKey() const
    {
        return key;
    }

    std::string getValue() const
    {
        return value;
    }

    std::string getString() const
    {
        return key + std::string(": ") + value;
    }

private:
    std::string key;
    std::string value;
};

using HttpHeaders = std::vector<HttpHeader>;

#endif
