export const steelRealtimeRoutes = [
  {
    path: '/steel-realtime',
    name: 'SteelRealtime',
    component: () => import('../views/steel-realtime/index.vue'),
    meta: {
      title: '钢铁全流程异常预警溯源',
      icon: 'ant-design:deployment-unit-outlined',
      orderNo: 20,
    },
  },
];
