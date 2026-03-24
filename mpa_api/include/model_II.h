#pragma once

#include <stdint.h>
#ifdef MODELII_EXPORTS
#define MPAMODEL_API __declspec(dllexport)
#else
#define MPAMODEL_API __declspec(dllimport)
#endif

typedef float SAMPLE_TYPE;

/*
* 设备添加事件，表示有新的设备可用
* 无参数，设备id在回调接口参数中
*/
#define EVENT_DEVICE_ADD	0x100

/*
* 设备移除事件，表示有设备被移除，不可用
* 无参数，设备id在回调接口参数中。
*/
#define EVENT_DEVICE_REMOVE	0x200
/*
* 测试数据事件，传输测试数据
* param1：数据缓冲区地址，数据类型为MpaSample数组
* param2：有效采样数
*/
#define EVENT_DATA_RECEIVED	0x300
/*
* 设备状态改变事件
*/
#define EVENT_STATUS_CHANGE 0x400

#ifdef __cplusplus

typedef uint64_t u64;
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int64_t i64;
typedef int32_t i32;
typedef int16_t i16;
typedef int8_t i8;

#define EC_OK		0
#define EC_CONTINUE	1
#define EC_ERROR	-1

extern "C" {
#endif
#pragma pack(push)
#pragma pack(1)
	typedef struct {
		float current; //电流，单位mA
		float voltage; //电压，单位V
	}MpaSample;
	typedef struct {
		float current; //电流，单位mA
		float voltage; //电压，单位V
//		float voltage2; //外部电压采集通道，单位V
	}MpaSample2;
#pragma pack(pop)

	/*
	* 回调接口，回调不在主线程中，注意相关保护和处理
	* 返回值：0成功，负值失败
	* user：使用MpaSetCallback设置回调接口时指定的用户数据，回调发生时原样回传
	* id：设备id
	* what：回调事件，参见事件定义
	* param1：事件参数，参见事件定义
	* param2：事件参数，参见事件定义
	*/
	typedef  uint64_t (WINAPI *DeviceCallback)(uint64_t user, uint64_t id, uint32_t what, uint64_t param1, uint64_t param2);

	/*
	* 枚举设备接口
	* 返回值：设备数，负值失败
	* pbuf：接收设备id的缓冲区，设备id为64位整数
	* len：缓冲区长度，能容纳64位整数的个数
	*/
	MPAMODEL_API int64_t WINAPI MpaEnum(uint64_t* pbuf, uint32_t len);


	/*
	* 启动测试接口
	* 返回值：0成功，负值失败
	* id：设备id
	* vol：输出电压，单位V，只对带电源的产品有效，无电源产品建议为0
	*/
	MPAMODEL_API int64_t WINAPI MpaStart(uint64_t id,float vol);

	/*
	* 停止测试接口
	* 返回值：0成功，负值失败
	* id：设备id
	*/
	MPAMODEL_API int64_t WINAPI MpaStop(uint64_t id);

	/*
	* 设置回调接口，只支持一个回调接口，多次设置以最后设置为准，可设置为NULL关闭回调。程序退出时，建议先关闭回调
	* 返回值：0成功，负值失败
	* fn：回调函数，参见DeviceCallback定义
	* user：用户数据，回调发生时原样回传
	*/
	MPAMODEL_API int64_t WINAPI MpaSetCallback(DeviceCallback fn, uint64_t user);
	
	/*
	* 获取数据
	* 返回值：获取到的采样数，一定低于或等于参数len
	* id：设备id
	* pcur：电流数据缓冲区，空间必须由调用者分配，并且有效空间必须大于len个float
	* pvol：电压数据缓冲区，空间必须由调用者分配，并且有效空间必须大于len个float
	* len：缓冲区大小，可使用的float个数
	*/
	MPAMODEL_API int64_t WINAPI MpaGetData(uint64_t id, float* pcur, float* pvol, uint32_t len );
/*
* 设置电压，仅对带电源的机型有效
* 返回值：0成功，负值失败
* id：设备id
* vol：电压值，单位伏特
*/	
	MPAMODEL_API int64_t WINAPI MpaSetVoltage(uint64_t id, float vol);

/*
* 关闭电源输出
* 返回值：0成功，负值失败
* id：设备id
*/	
	MPAMODEL_API int64_t WINAPI MpaOutputOff(uint64_t id);



#ifdef __cplusplus
}
#endif

