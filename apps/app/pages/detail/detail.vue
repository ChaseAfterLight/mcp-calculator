<template>
  <view class="device-wrapper">
    <!-- Header Controls -->
    <view class="device-header">
       <view class="header-leds">
         <view class="led red-led blinking"></view>
         <text class="glitch-title">深度分析模式 // ANALYSIS</text>
       </view>
       <view class="screen-btn" @click="goBack">
          <text>◀ 退出</text>
       </view>
    </view>

    <!-- Main Scanner Screen -->
    <view class="hardware-screen bezel">
      <view class="scanner-display">
        <view class="scanline"></view>
        <view class="crosshair-tl"></view>
        <view class="crosshair-tr"></view>
        <view class="crosshair-bl"></view>
        <view class="crosshair-br"></view>
        
        <view class="img-container" v-if="species && species.image_url" @click="previewImage">
          <image class="scan-target" :src="species.image_url" mode="aspectFill"></image>
          <!-- HUD Overlays -->
          <view class="hud-box target-hud">目标已锁定 // LOCKED</view>
          <view class="hud-line"></view>
        </view>
        
        <view v-else-if="loading" class="terminal-text">
           <text class="blinking-cursor">正在扫描周围环境...</text>
        </view>
      </view>
    </view>

    <!-- Data Panel / Specs -->
    <view class="data-panel" v-if="species">
      
      <!-- ID Label -->
      <view class="spec-plate primary-plate">
        <view class="plate-top">
          <text class="sys-id">档案编号: {{ cardId.slice(-8).toUpperCase() || 'UNKNOWN' }}</text>
          <view class="rarity">评级: <text v-for="n in (species.rarity || 3)" :key="n" class="star">★</text></view>
        </view>
        <text class="zh-name">{{ species.chinese_name }}</text>
        <text class="en-name">{{ species.latin_name }}</text>
        <view class="tags-row mt-10">
          <text class="hardware-tag type-bg">{{ getCategoryName(species.category) }}</text>
          <text class="hardware-tag alert-bg" v-if="species.protection_level">保护等级: {{ species.protection_level }}</text>
        </view>
      </view>

      <!-- Grid Specs -->
      <view class="spec-grid">
        <view class="spec-box" v-if="species.habitat">
          <text class="spec-lbl">HABITAT // 栖息地</text>
          <text class="spec-val">{{ species.habitat }}</text>
        </view>
        <view class="spec-box" v-if="species.observation_season">
          <text class="spec-lbl">SEASON // 周期</text>
          <text class="spec-val">{{ species.observation_season }}</text>
        </view>
      </view>

      <!-- Features Terminal Box -->
      <view class="terminal-box" v-if="species.features && species.features.length">
        <view class="term-header">>>> 观测到的生物特征</view>
        <view class="term-body">
          <text class="term-list" v-for="(feat, fIdx) in species.features" :key="fIdx">>- {{ feat }}</text>
        </view>
      </view>

      <view class="terminal-box log-box" v-if="species.fun_fact">
        <view class="term-header">>>> 观测备注</view>
        <view class="term-body">
          <text class="term-text">{{ species.fun_fact }}</text>
        </view>
      </view>

      <!-- Hardware Action Panel -->
      <view class="action-panel">
         <text class="action-title">>>> 实体档案转换</text>
         
         <view class="card-preview-area" v-if="species.card_image_url" @click="previewCardImage">
           <image class="holo-card" :src="species.card_image_url" mode="widthFix"></image>
           <view class="holo-effect"></view>
         </view>
      </view>

    </view>

    <!-- Bottom Physical Buttons -->
    <view class="physical-controls" v-if="species">
      <view class="hardware-btn btn-print" @click="toShare">
         <text class="btn-text">数据分享</text>
      </view>
      <view class="hardware-btn btn-regen" @click="regenerateCard">
         <text class="btn-text">重新扫描</text>
      </view>
    </view>

  </view>
</template>

<script>
const API_BASE = 'http://127.0.0.1:8000/api';
const SERVER_BASE = API_BASE.replace(/\/api$/, '');

export default {
  data() {
    return {
      species: null,
      loading: true,
      cardId: ''
    }
  },
  onLoad(options) {
    if (options.card_id) {
      this.cardId = decodeURIComponent(options.card_id);
      this.loadDetail();
      return;
    }

    if (options.data) {
      try {
        this.species = this.normalizeSpecies(JSON.parse(decodeURIComponent(options.data)));
        this.cardId = this.species.card_id || '';
      } catch (e) {
        console.error(e);
      }
    }

    this.loading = false;
  },
  methods: {
    goBack() { uni.navigateBack(); },
    async loadDetail() {
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/${encodeURIComponent(this.cardId)}`,
          method: 'GET'
        });
        const res = Array.isArray(response) ? response[1] : response;
        if (res?.data?.success) {
          this.species = this.normalizeSpecies(res.data.data || {});
        } else {
          this.species = null;
        }
      } catch (e) {
        console.error(e);
        this.species = null;
      } finally {
        this.loading = false;
      }
    },
    normalizeSpecies(raw) {
      const species = raw || {};
      const displayImagePath = species.source_image_path || species.image_path || '';
      return {
        ...species,
        features: Array.isArray(species.features) ? species.features : [],
        image_url: this.toImageUrl(displayImagePath || species.image_url || ''),
        card_image_url: this.toImageUrl(species.card_image_path || species.image_path || ''),
        created_at: species.created_at || species.generated_at || ''
      };
    },
    getCategoryName(val) {
      const map = { plant: '草本植物', animal: '野生生物', mineral: '无机矿石' };
      return map[val] || val || '未知成分';
    },
    previewImage() {
      if (this.species && this.species.image_url) {
        uni.previewImage({ urls: [this.species.image_url] });
      }
    },
    previewCardImage() {
      if (this.species && this.species.card_image_url) {
        uni.previewImage({ urls: [this.species.card_image_url] });
      }
    },
    toShare() {
      uni.navigateTo({
        url: `/pages/share/share?card_id=${this.cardId}&chinese_name=${encodeURIComponent(this.species.chinese_name)}`
      });
    },
    async regenerateCard() {
      uni.showLoading({ title: '执行重新扫描...' });
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/generate-card`,
          method: 'POST',
          data: {
            card_id: this.cardId,
            chinese_name: this.species.chinese_name,
            latin_name: this.species.latin_name,
            features: this.species.features || ['未知'],
            category: this.species.category || "plant",
            habitat: this.species.habitat || "",
            observation_season: this.species.observation_season || "",
            protection_level: this.species.protection_level || "",
            fun_fact: this.species.fun_fact || "",
            rarity: this.species.rarity || 3
          }
        });
        const res = Array.isArray(response) ? response[1] : response;
        uni.hideLoading();
        if (res && res.data && res.data.success) {
          await this.loadDetail();
          uni.showToast({ title: '档案已更新', icon: 'success' });
        } else {
          uni.showToast({ title: '扫描失败', icon: 'none' });
        }
      } catch (e) {
        uni.hideLoading();
        uni.showToast({ title: '通讯中断', icon: 'none' });
      }
    },
    toImageUrl(imagePath) {
      if (!imagePath) return '';
      if (/^https?:\/\//.test(imagePath)) return imagePath;
      const normalized = String(imagePath).replace(/\\/g, '/').replace(/^\/+/, '');
      return `${SERVER_BASE}/${normalized}`;
    }
  }
}
</script>

<style lang="scss">
page { 
  background-color: #A9262C; 
}

.device-wrapper {
  background-color: #D32F2F;
  min-height: 100vh;
  padding-bottom: 90px;
  box-shadow: inset 0 0 20px rgba(0,0,0,0.3);
}

.device-header {
  padding: 40px 20px 15px;
  background: linear-gradient(180deg, #E53935 0%, #D32F2F 100%);
  border-bottom: 3px solid #B71C1C;
  display: flex; justify-content: space-between; align-items: center;
}

.header-leds { display: flex; align-items: center; gap: 10px; }
.led { width: 12px; height: 12px; border-radius: 50%; border: 1px solid #212121; }
.red-led { background: #EF5350; box-shadow: 0 0 5px #EF5350; }
@keyframes blinkled { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
.blinking { animation: blinkled 1s infinite; }

.glitch-title { font-size: 16px; font-weight: bold; color: #FFF; text-shadow: 1px 1px 0 #212121; }

.screen-btn {
  background: #212121; border: 2px solid #000; padding: 4px 8px; border-radius: 4px;
  color: #FFF; font-size: 10px; font-weight: bold; box-shadow: 0 2px 0 #000;
}
.screen-btn:active { transform: translateY(2px); box-shadow: 0 0 0 #000; }

/* 扫描屏幕区域 */
.hardware-screen {
  background-color: #E0E0E0; margin: 15px 20px; padding: 10px;
  border-radius: 12px; border: 2px solid #757575;
  box-shadow: inset 0 2px 5px rgba(0,0,0,0.2), 0 5px 10px rgba(0,0,0,0.3);
}

.scanner-display {
  background-color: #000; border-radius: 6px; position: relative;
  height: 220px; overflow: hidden; border: 2px inset #424242;
}

.scanline {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 255, 0, 0.04) 50%);
  background-size: 100% 4px; pointer-events: none; z-index: 10;
}

/* 屏幕四角瞄准星 */
.crosshair-tl { position: absolute; top: 10px; left: 10px; border-top: 2px solid #0F0; border-left: 2px solid #0F0; width: 20px; height: 20px; z-index: 10;}
.crosshair-tr { position: absolute; top: 10px; right: 10px; border-top: 2px solid #0F0; border-right: 2px solid #0F0; width: 20px; height: 20px; z-index: 10;}
.crosshair-bl { position: absolute; bottom: 10px; left: 10px; border-bottom: 2px solid #0F0; border-left: 2px solid #0F0; width: 20px; height: 20px; z-index: 10;}
.crosshair-br { position: absolute; bottom: 10px; right: 10px; border-bottom: 2px solid #0F0; border-right: 2px solid #0F0; width: 20px; height: 20px; z-index: 10;}

.img-container { width: 100%; height: 100%; position: relative; }
.scan-target { width: 100%; height: 100%; opacity: 0.9; }

.hud-box { position: absolute; font-family: monospace; font-size: 10px; color: #0F0; background: rgba(0,255,0,0.2); padding: 2px 5px; border: 1px solid #0F0; z-index: 10;}
.target-hud { bottom: 15px; left: 15px; }

@keyframes scan-animate { 0% { top: 0; } 50% { top: 100%; } 100% { top: 0; } }
.hud-line { position: absolute; top: 0; left: 0; width: 100%; height: 2px; background: rgba(0, 255, 0, 0.5); box-shadow: 0 0 10px #0F0; animation: scan-animate 3s linear infinite; z-index:9;}

.terminal-text { padding: 30px; color: #0F0; font-size: 12px; font-weight: bold; position: relative; z-index:1;}

/* 数据面板 */
.data-panel { margin: 0 20px; }

.spec-plate {
  background: #E0E0E0; border: 2px solid #424242; box-shadow: 2px 2px 0 #424242;
  border-radius: 6px; padding: 12px; margin-bottom: 15px;
}
.plate-top { display: flex; justify-content: space-between; border-bottom: 1px dashed #757575; padding-bottom: 5px; margin-bottom: 8px;}
.sys-id { font-size: 10px; font-weight: bold; color: #616161; }
.rarity { font-size: 10px; font-weight: bold; color: #D32F2F; }
.star { margin-left:2px; }

.zh-name { font-size: 20px; font-weight: 900; color: #212121; display: block; margin-bottom: 2px; }
.en-name { font-size: 12px; color: #616161; font-weight: bold; display: block; }

.mt-10 { margin-top: 10px; }
.tags-row { display: flex; gap: 10px; }
.hardware-tag { font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: bold; color: white; border: 1px solid rgba(0,0,0,0.5); box-shadow: inset 0 1px 2px rgba(255,255,255,0.3); }
.type-bg { background: #4FC3F7; color: #01579B; border-color: #0288D1; }
.alert-bg { background: #EF5350; }

.spec-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }
.spec-box { background: #E0E0E0; border: 2px solid #424242; box-shadow: 2px 2px 0 #424242; padding: 8px; border-radius: 4px; display: flex; flex-direction: column;}
.spec-lbl { font-size: 9px; font-weight: bold; color: #757575; margin-bottom: 4px; }
.spec-val { font-size: 12px; font-weight: bold; color: #212121; }

.terminal-box {
  background: #0F380F; border: 2px solid #212121; border-radius: 6px; margin-bottom: 15px;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.8); padding: 10px;
}
.log-box { background: #424242; } /* 不同底色表示不同模块 */

.term-header { color: #9BBC0F; font-size: 10px; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #306230; padding-bottom: 4px; }
.log-box .term-header { color: #FFCC00; border-bottom-color: #616161; }

.term-body { display: flex; flex-direction: column; gap: 4px;}
.term-list { color: #9BBC0F; font-size: 12px; font-weight: bold; }
.term-text { color: #FFF; font-size: 12px; line-height: 1.4; font-weight: normal;}

.action-panel {
  background: #E0E0E0; border: 2px dashed #757575; padding: 12px; border-radius: 6px;
  text-align: center; margin-bottom: 20px;
}
.action-title { font-size: 10px; font-weight: bold; color: #616161; display: block; margin-bottom: 10px; }

.card-preview-area {
  position: relative; border: 4px solid #212121; border-radius: 8px; overflow: hidden;
  background: #000; box-shadow: 0 5px 15px rgba(0,0,0,0.5); display: inline-block; width: 80%;
}
.holo-card { width: 100%; display: block; }
.holo-effect { position: absolute; top:0; left:0; right:0; bottom:0; background: linear-gradient(125deg, rgba(255,255,255,0.3) 0%, transparent 40%, rgba(255,255,255,0.1) 60%, transparent 100%); pointer-events: none;}

/* 固定底部按钮 */
.physical-controls {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: #D32F2F; padding: 15px 20px;
  display: flex; gap: 15px;
  box-shadow: 0 -4px 10px rgba(0,0,0,0.3); border-top: 3px solid #B71C1C;
  padding-bottom: calc(15px + env(safe-area-inset-bottom)); z-index: 100;
}

.hardware-btn {
  flex: 1; padding: 12px 0; border-radius: 8px; text-align: center;
  box-shadow: 0 4px 0 #111, 0 6px 10px rgba(0,0,0,0.3); border: 2px solid #212121;
}
.hardware-btn:active { transform: translateY(4px); box-shadow: 0 0 0 #000; }

.btn-print { background: #1E88E5; }
.btn-regen { background: #FFCA28; }

.btn-text { color: #FFF; font-size: 14px; font-weight: 900; text-shadow: 1px 1px 0 #000; }
.btn-regen .btn-text { color: #212121; text-shadow: none; }

@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.blinking-cursor::after { content: '_'; animation: blink 1s step-end infinite; }
</style>
