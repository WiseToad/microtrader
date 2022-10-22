#ifndef CURLEXT_H
#define CURLEXT_H

#include <curl/curl.h>
#include <memory>

using CurlEasyPtr = std::unique_ptr<CURL, void(*)(CURL *)>;

struct CurlGlobal
{
    CurlGlobal() = default;
    CurlGlobal(const CurlGlobal &) = delete;
    CurlGlobal & operator = (const CurlGlobal &) = delete;

    bool init()
    {
        if(!isInit) {
            isInit = (curl_global_init(CURL_GLOBAL_DEFAULT) == CURLE_OK);
        }
        return isInit;
    }

    CurlEasyPtr easyInit()
    {
        return CurlEasyPtr(init() ? curl_easy_init() : nullptr, curl_easy_cleanup);
    }

    ~CurlGlobal()
    {
        if(isInit) {
            curl_global_cleanup();
            isInit = false;
        }
    }

private:
    bool isInit = false;

};

struct CurlSlist
{
    CurlSlist():
        listPtr(nullptr, curl_slist_free_all)
    {}

    curl_slist *get() const
    {
        return listPtr.get();
    }

    operator bool () const
    {
        return bool(listPtr);
    }

    bool add(const char *str)
    {
        curl_slist *newPtr = curl_slist_append(listPtr.get(), str);
        if(newPtr) {
            listPtr.release();
            listPtr.reset(newPtr);
            return true;
        } else {
            return false;
        }
    }

private:
    std::unique_ptr<curl_slist, void(*)(curl_slist *)> listPtr;
};

struct CurlExec
{
    bool operator () (CURLcode result)
    {
        this->result = result;
        return result == CURLE_OK;
    }

    operator bool () const
    {
        return result == CURLE_OK;
    }

    CURLcode getResult()
    {
        return result;
    }

private:
    CURLcode result = CURLE_OK;
};

#endif
