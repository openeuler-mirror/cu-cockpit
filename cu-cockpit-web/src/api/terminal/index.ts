import request from '/@/utils/request';
import Cookies from 'js-cookie'

type connectType = {
  hostname: string,
  port: number,
  username: string,
  password: string,
  term: string
}
/**
 * 终端认证
 * @param data
 * @returns 
 */
export const connect = (data: connectType) => {
  return request({
    url: '/terminal/connect',
    method: 'post',
    headers: { 
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-CSRFToken': Cookies.get('csrftoken')
    },
    data
  });
}

/**
 * 检查是否登录
 * @returns 
 */
export const check = () => {
  return request({
    url: '/terminal/check',
    method: 'get',
  });
}

/**
 * 获取终端token
 * @returns 
 */
export const getToken = () => {
  return request({
    url: '/terminal/token',
    method: 'get',
  });
}

