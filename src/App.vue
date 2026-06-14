<script setup lang="ts">
import { onMounted, ref } from 'vue'

//chart
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
use([
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  CanvasRenderer
])



const DATA_FOLDER = `./marketdata`;
const MWI_JSON_PATH = "https://www.milkywayidle.com/game_data/marketplace.json";
const INDEX_FILE = `index.json`;

//市场数据
interface Market {
  marketData: { [key: string]: { [key: string]: MarketItem } };
  timestamp: number;
}
interface MarketItem {
  a?: number;
  b?: number;
  p?: number;
  v?: number;
}
let allMarketData = new Map<number, Market>();
//获取所有文件列表
async function getMarketFileList(): Promise<string[]> {
  const url = `${DATA_FOLDER}/${INDEX_FILE}`;
  try {
    const response = await fetch(url);
    // 1. 检查网络请求是否成功
    if (!response.ok) {
      throw new Error(`Failed to fetch file list: ${response.status} ${response.statusText}`);
    }
    // 2. 解析 JSON 数据
    const data = await response.json();
    // 3. 简单校验数据结构是否符合预期
    if (!Array.isArray(data)) {
      console.warn('Expected an array but received:', typeof data);
      return []; // 或者抛出特定错误
    }
    return data as string[];
  } catch (error) {
    // 4. 捕获网络错误或 JSON 解析错误
    console.error('Error fetching market file list:', error);
    throw error; // 根据业务需求决定是抛出异常还是返回空数组
  }
}
//按列表获取所有市场数据生成map
async function fetchMarketData(filelist: string[]): Promise<void> {
  let ret: Map<number, Market> = new Map();

  // 1. 使用 map 生成一个包含所有 fetch 请求的 Promise 数组
  const promises = filelist.map(async (file) => {
    try {
      const filepath = `${DATA_FOLDER}/${file}`;
      const response = await fetch(filepath);
      if (!response.ok) throw new Error(`HTTP错误: ${response.status}`);
      const data = await response.json();

      // 2. 数据解析成功后，存入 Map
      ret.set(data["timestamp"], data);
    } catch (error) {
      console.error(`文件 ${file} 获取失败:`, error);
    }
  });

  // 3. 核心：等待所有 Promise 全部执行完毕
  await Promise.all(promises);

  // 4. 此时所有数据都已下载完成，再返回 Map
  allMarketData = ret;
  return;
}

//日期选择器选择结果，以timestamp为单位
const sliderSelectValue = ref([0, 0]);
//日期选择器可以选择的时间点，以timestamp为单位
const sliderMarks = ref<Record<number, string>>({});
//日期选择器范围
const sliderMin = ref(0);
const sliderMax = ref(0);
//提示信息
const sliderHint = ref("");
//秒数差格式化为xxx天以前
function formatSecondsAgo(timestamp: number): string {
  let seconds = Date.now() / 1000 - timestamp;
  if (seconds < 0) return '刚刚'
  const day = Math.floor(seconds / 86400)
  const hour = Math.floor((seconds % 86400) / 3600)
  const minute = Math.floor((seconds % 3600) / 60)

  const parts = []
  if (day) parts.push(`${day}天`)
  if (hour) parts.push(`${hour}时`)
  if (minute) parts.push(`${minute}分`)
  return parts.length ? `${parts.join('')}前` : '刚刚'
}
//初始化滑块
function initSlider() {
  for (let timestamp of allMarketData.keys()) {
    sliderMarks.value[timestamp] = formatSecondsAgo(timestamp);
  }
  sliderMin.value = Math.min(...allMarketData.keys());
  sliderMax.value = Math.max(...allMarketData.keys());
  sliderSelectValue.value = [Math.min(...allMarketData.keys()), Math.max(...allMarketData.keys())]
}


//表格数据显示
//表格显示定义
interface ItemDisplayData {
  name: string
  lowPrice: number,
  avgPrice: number,
  highPrice: number,
  totalAmount: number,
  lowAmount: number,
  highAmount: number,
}
let displaydatas = ref<ItemDisplayData[]>([]);
//利用平均价格 计算买卖填单数
function getLowRatio(low: number, avg: number, high: number): number {
  return (high - avg) / (high - low);
}
//解析数据并显示表格
function displayTableData(items: string[], timestamps: number[]): void {
  //按照items寻找各数据时间
  let ret: ItemDisplayData[] = [];
  for (const item of items) {
    //总销售量
    let totalAmount = 0;
    //低价(左)填单卖数量
    let lowAmount = 0;
    //高价(右)填单卖数量
    let highAmount = 0;
    //最低价格
    let lowPrice = -100;
    //最高价格
    let highPrice = -100;
    //总花费钱数 用于计算
    let totalMoney = -100;
    //总包数 一个包是6小时数据
    let packCnt = 0;
    //遍历所有时间戳数据
    for (const timestamp of timestamps) {
      let marketitem = allMarketData.get(timestamp)?.marketData[`/items/${item}`]?.["0"];
      if (!marketitem || !marketitem.a || !marketitem.b || !marketitem.p || !marketitem.v) {
        continue;
      }
      let ratio = getLowRatio(marketitem.b, marketitem.p, marketitem.a);

      totalAmount += marketitem.v;
      lowAmount += marketitem.v * ratio;
      highAmount += marketitem.v * (1 - ratio);
      lowPrice = lowPrice < 0 ? marketitem.b : Math.min(lowPrice, marketitem.b);
      highPrice = highPrice < 0 ? marketitem.a : Math.max(highPrice, marketitem.a);
      totalMoney += marketitem.v * marketitem.p;
      packCnt++;
    }
    //更新显示 涉及到量平均到一天
    let displaydata: ItemDisplayData = {
      name: item,
      lowPrice: lowPrice,
      avgPrice: totalMoney / totalAmount,
      highPrice: highPrice,
      totalAmount: totalAmount / packCnt * 24,
      lowAmount: lowAmount / packCnt * 24,
      highAmount: highAmount / packCnt * 24,
    }
    ret.push(displaydata);
  }
  displaydatas.value = ret;
  return;
}

//显示图表
const option = ref({});
function displayChartData(item: string): void {
  //获取数据
  let timestamps: number[] = [...allMarketData.keys()];
  let lowPrice: number[] = [];
  let avgPrice: number[] = [];
  let highPrice: number[] = [];
  let totalAmount: number[] = [];
  let lowAmount: number[] = [];
  let highAmount: number[] = [];

  for (let timestamp of timestamps) {
    let marketitem = allMarketData.get(timestamp)?.marketData[`/items/${item}`]?.["0"];
    if (!marketitem || !marketitem.a || !marketitem.b || !marketitem.p || !marketitem.v) {
      continue;
    }
    lowPrice.push(marketitem.b);
    avgPrice.push(marketitem.p);
    highPrice.push(marketitem.a);
    totalAmount.push(marketitem.v);
    let ratio = getLowRatio(marketitem.b, marketitem.p, marketitem.a);
    lowAmount.push(marketitem.v * ratio);
    highAmount.push(marketitem.v * (1 - ratio));

    option.value = {
      title: { text: `${item}价格与销量趋势图`, left: 'center' },
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      legend: { data: ['低价', '均价', '高价', '低价销量', '高价销量', '总销量'], left: 'left' },
      xAxis: [{ type: 'category', data: timestamps, axisLabel: { formatter: (value: number) => { return formatSecondsAgo(value) } } }],
      yAxis: [
        { type: 'value', name: '价格', min: 'dataMin', max: 'dataMax' },
        { type: 'value', name: '销量', position: 'right', min: 'dataMin', max: 'dataMax' }
      ],
      series: [
        { name: '低价', type: 'line', color: '#36b37e', yAxisIndex: 0, data: lowPrice, lineStyle: { type: [8, 4], width: 2 } },
        { name: '均价', type: 'line', color: '#0065ff', yAxisIndex: 0, data: avgPrice, lineStyle: { type: [8, 4], width: 2 } },
        { name: '高价', type: 'line', color: '#ff5630', yAxisIndex: 0, data: highPrice, lineStyle: { type: [8, 4], width: 2 } },
        { name: '低价销量', type: 'line', color: '#36b37e', yAxisIndex: 1, data: lowAmount },
        { name: '高价销量', type: 'line', color: '#ff5630', yAxisIndex: 1, data: highAmount },
        { name: '总销量', type: 'line', color: '#0065ff', yAxisIndex: 1, data: totalAmount },
      ]
    };

  }

}

//表格点击事件
function onTableRowClicked(row: any, column: any, event: Event): void {
  const firstColValue = row.name;
  displayChartData(firstColValue);
}




//滑块移动事件
function onSliderChanged(range: number[]): void {
  const [start, end] = range;
  if (start === undefined || end === undefined) return;
  //1.获取有效数据量并显示
  let timestamps: number[] = [...allMarketData.keys()].filter(t => (t >= start) && (t <= end));
  sliderHint.value = `总共数据为${timestamps.length}个 时长为${timestamps.length}小时 时间范围为${new Date(start * 1000).toLocaleString('zh-CN')}-${new Date(end * 1000).toLocaleString('zh-CN')}`;
  //2.更新表格
  displayTableData([
    "ultra_attack_coffee",
    "ultra_melee_coffee",
    "ultra_ranged_coffee",
    "ultra_magic_coffee",
    "sunstone",
    "crushed_sunstone",
  ], timestamps);
}
onMounted(() => {
  getMarketFileList()
    .then((filelist) => fetchMarketData(filelist))
    .then(() => {      
      initSlider();
      const keysArr = [...allMarketData.keys()]; // 只生成一次数组
      if (keysArr.length !== 0) {
        const first = keysArr.at(0)!;
        const last = keysArr.at(-1)!;
        onSliderChanged([first, last]);
      }})
    .catch((error) => console.error("Error:", error));
});

</script>

<template>
  <h1>
    欢迎来到销量统计器！
  </h1>
  <div class="slider-wrapper">
    <br>时间选择</br>
    <br> {{ sliderHint }} </br>
    <el-slider v-model="sliderSelectValue" range :marks="sliderMarks" step="mark" :min="sliderMin" :max="sliderMax"
      :format-tooltip="formatSecondsAgo" @change="onSliderChanged" show-stops />
  </div>
  <div>
    <span>平均每天数据</span>
    <el-table :data="displaydatas" height="400" style="width: 100%" @row-click="onTableRowClicked">
      <el-table-column label="名称" prop="name" width="180" />
      <el-table-column label="低价" prop="lowPrice" width="180" />
      <el-table-column label="高价" prop="highPrice" width="180" />
      <el-table-column label="交易均价" prop="avgPrice" width="180" />
      <el-table-column label="销售总量" prop="totalAmount" width="180" />
      <el-table-column label="低价交易量" prop="lowAmount" width="180" />
      <el-table-column label="高价交易量" prop="highAmount" width="180" />
    </el-table>
  </div>
  <div class="chart-box">
    <VChart :option="option" style="width: 100%; height: 450px;" />
  </div>
</template>

<style scoped>
.slider-wrapper {
  width: 80%;
  margin: 0 auto;
  /* 左右留空 */
}

.chart-box {
  padding: 20px;
}
</style>
