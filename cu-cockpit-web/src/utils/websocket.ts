import {ElNotification  as message} from 'element-plus'
import {Session} from "/@/utils/storage";
import {getWsBaseURL} from "/@/utils/baseUrl";
import socket from '/@/types/socket'

const websocket: socket = {
    websocket: null,
    connectURL: getWsBaseURL(),
    // 开启标识
    socket_open: false,
    // 心跳timer
    hearbeat_timer: 0,
    // 心跳发送频率
    hearbeat_interval: 2 * 1000,
    // 是否自动重连
    is_reconnect: false,
    // 重连次数
    reconnect_count: 0,
    // 已发起重连次数
    reconnect_current: 1,
    // 重连timer
    reconnect_timer: 0,
    // 重连频率
    reconnect_interval: 5 * 1000,
    // eslint-disable-next-line no-unused-vars
    init: (receiveMessage: ((_msg: { data: Blob }) => void) | null, closeCallback: (() => void) | null, wsUrl: string) => {
        if (!('WebSocket' in window)) {
            message.warning('浏览器不支持WebSocket')
            return null
        }
        const token = Session.get('token')
        if(!token){
            // message.warning('websocket认证失败')
            return null
        }
        // const wsUrl = `${getWsBaseURL()}ws/${token}/`
        console.log('wsUrl: ', wsUrl)
        websocket.websocket = new WebSocket(wsUrl)
        websocket.websocket.onmessage = (e) => {
            if (receiveMessage) {
                receiveMessage(e)
            }
        }
        websocket.websocket.onclose = (e) => {
            console.log('websocket close: ', e)
            websocket.socket_open = false
            if (closeCallback) {
                closeCallback();
            }
            // 需要重新连接
            if (websocket.is_reconnect) {
                websocket.reconnect_timer = setTimeout(() => {
                    // 超过重连次数
                    if (websocket.reconnect_current > websocket.reconnect_count) {
                        clearTimeout(websocket.reconnect_timer)
                        websocket.is_reconnect = false
                        websocket.socket_open = false
                        return
                    }
                    // 记录重连次数
                    websocket.reconnect_current++
                    websocket.reconnect()
                }, websocket.reconnect_interval)
            }
        }
        // 连接成功
        websocket.websocket.onopen = function () {
            websocket.socket_open = true
            websocket.is_reconnect = true
            // 开启心跳
            // websocket.heartbeat()
        }
        // 连接发生错误
        websocket.websocket.onerror = function (e) {
          console.log('WebSocket onerror', e)
        }
    },
    heartbeat: () => {
        if (websocket.hearbeat_timer) {
            clearInterval(websocket.hearbeat_timer);
        }

        websocket.hearbeat_timer = setInterval(() => {
            const data = {
                token: Session.get('token')
            }
            websocket.send(data)
        }, websocket.hearbeat_interval)
    },
    send: (data:string, callback = null) => {
        // 开启状态直接发送
        if (websocket.websocket && websocket.websocket.readyState === websocket.websocket.OPEN) {
            // websocket.websocket.send(JSON.stringify(data))
            websocket.websocket.send(data)
            if (callback) {
                callback();
            }
        } else {
            clearInterval(websocket.hearbeat_timer)
            // message({
            //     type: 'warning',
            //     message: 'socket链接已断开',
            //     duration: 1000,
            // })
            websocket.socket_open = false
        }
    },
    close: () => {
        websocket.is_reconnect = false
        websocket.websocket?.close()
        websocket.websocket = null;
        websocket.socket_open = false
    },
    /**
     * 重新连接
     */
    reconnect: () => {
        if (websocket.websocket && !websocket.is_reconnect) {
            websocket.close()
        }
        websocket.init(null)
    },
}
export default websocket;
