// model_test.cpp : 此文件包含 "main" 函数。程序执行将在此处开始并结束。
//
#define _CRT_SECURE_NO_WARNINGS
#include <iostream>
#include <Windows.h>
//接口说明在model_ii.h文件中
#include "../include/model_ii.h"
#ifdef _WIN64
#pragma comment( lib,"lib64/model_ii.lib")
#else
#pragma comment( lib,"lib32/model_ii.lib")
#endif
using namespace std;
//获取数据
float watch(MpaSample* psample, u64 count, float* pvol, float* pcur)
{
    double vol = 0;
    double cur = 0;
    //cout << "count = " << count << endl;

    for (int i = 0; i < count; i++)
    {
        vol += psample[i].voltage;
        cur += psample[i].current;
    }
    *pvol = vol / count;
    *pcur = cur / count;
    return *pcur;
}

//回调函数，仅处理获取数据事件
uint64_t WINAPI Callback(uint64_t user, uint64_t id, uint32_t what, uint64_t param1, uint64_t param2)
{
    if (what != EVENT_DATA_RECEIVED)
    {
        return 0;
    }
    static uint64_t bs = 0;
    static uint64_t count = 0;
    count += param2;
    uint64_t t = count / 1600;
    float vavg, cavg;
    watch((MpaSample*)param1,param2,&vavg,&cavg);
    //计数减少打印次数
    if (t > bs)
    {
        bs = t;
        cout << "recive block count=" << bs << endl;
        cout << "vol=" << vavg << "     cur=" << cavg << endl;
    }
//    Sleep(100);
    return 0;
}

uint64_t devices[10];

void GetDataTest()
{
    for (int i = 0; i < 200; i++)
    {
        MpaStart(devices[0], 3.3);
        float total_vol;
        float total_cur;
        total_vol = 0;
        total_cur = 0;
        for (int j = 0; j < 300; j++)
        {
            int count;
            count = 0;
            float vol[100];
            float cur[100];
            memset(vol, 0, sizeof(float) * 100);
            memset(cur, 0, sizeof(float) * 100);
            while (count != 100)
            {
                int len = MpaGetData(devices[0], &cur[count], &vol[count], 100 - count);
                if (len > 0)
                {
                    count += len;
                }
            }
            float tvol = 0, tcur = 0;
            for (int k = 0; k < count; k++)
            {
                tvol += vol[k];
                tcur += cur[k];
            }
            total_vol += tvol / count;
            total_cur += tcur / count;
        }
        float avg_vol = total_vol / 300;
        float avg_cur = total_cur / 300;
        cout << "avg_vol=" << avg_vol << "\t\tavg_cur=" << avg_cur << endl;
        MpaStop(devices[0]);
        cout << "test_count=" << i + 1 << endl;
        Sleep(1000);
    }
}


int main()
{
    MpaSetCallback(Callback, 33);
    Sleep(3000);
    u64 count = MpaEnum(devices, 10);
    cout << "device count=" << count << endl;
    cout << "IDs:" << endl;
    for (int i = 0; i < count; i++)
    {
        std::cout << devices[i] << endl;
    }
    std::cout << "plugin device before start this program,1-start, 2-stop, 3-set voltage to 4.0v, 0-exit" << endl;
    while (1)
    {
        int cmd;
        scanf("%d", &cmd);
        if (cmd == 0)
        {
            break;
        }
        switch (cmd)
        {
        case 1:
            MpaStart(devices[0], 3.3f);
            break;
        case 2:
            MpaStop(devices[0]);
            break;
        case 3:
            MpaSetVoltage(devices[0], 4);
            break;
        case 4:
            GetDataTest();
            break;
        }
    }

    

}

