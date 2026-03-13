<template>
  <view class="container">
    <view class="header">
      <view class="title">记录新物种</view>
      <view class="subtitle">把你的发现添加到向导</view>
    </view>
    
    <scroll-view scroll-y class="form-container">
      <view class="form-item">
        <text class="label">中文名 *</text>
        <input class="input" v-model="form.chinese_name" placeholder="请输入物种名称" />
      </view>
      <view class="form-item">
        <text class="label">学名/拉丁名 *</text>
        <input class="input" v-model="form.latin_name" placeholder="对应的学名" />
      </view>
      <view class="form-item">
        <text class="label">分类 *</text>
        <picker @change="onCategoryChange" :value="catIndex" :range="categories" range-key="label">
          <view class="picker">{{ categories[catIndex].label }}</view>
        </picker>
      </view>
      <view class="form-item">
        <text class="label">显著特征（用逗号分隔） *</text>
        <input class="input" v-model="form.featuresStr" placeholder="如：黑色条纹, 体型小..." />
      </view>
      <view class="form-item">
        <text class="label">保护级别</text>
        <input class="input" v-model="form.protection_level" placeholder="(选填) 例如：国家一级" />
      </view>
      <view class="form-item">
        <text class="label">稀有度 (1-5)</text>
        <slider style="margin: 0" min="1" max="5" :value="form.rarity" @change="e => form.rarity = e.detail.value" show-value />
      </view>
      <view class="form-item">
        <text class="label">观察季节</text>
        <input class="input" v-model="form.observation_season" placeholder="(选填) 例如：春季" />
      </view>
      <view class="form-item">
        <text class="label">趣味冷知识</text>
        <textarea class="textarea" v-model="form.fun_fact" placeholder="(选填) 记录你发现的有趣现象..." />
      </view>
    </scroll-view>

    <view class="footer">
      <view class="btn submit-btn" :class="{disabled: isSubmitting}" @click="submitRegister">
        {{ isSubmitting ? '正在生成卡片...' : '确认记录并生成卡片' }}
      </view>
    </view>
  </view>
</template>

<script>
const API_BASE = 'http://127.0.0.1:8000/api';

export default {
  data() {
    return {
      userId: 'default',
      isSubmitting: false,
      categories: [
        { value: 'plant', label: '植物 🌿' },
        { value: 'animal', label: '动物 🐾' },
        { value: 'mineral', label: '矿物 💎' }
      ],
      catIndex: 0,
      form: this.getInitialForm()
    }
  },
  methods: {
    getInitialForm() {
      return {
        chinese_name: '', latin_name: '', featuresStr: '',
        protection_level: '', observation_season: '', fun_fact: '', rarity: 3
      }
    },
    onCategoryChange(e) { this.catIndex = e.detail.value; },
    async submitRegister() {
      if (!this.form.chinese_name || !this.form.latin_name || !this.form.featuresStr) {
        uni.showToast({ title: '请填写带*的必填项', icon: 'none' });
        return;
      }
      if (this.isSubmitting) return;
      this.isSubmitting = true;

      const features = this.form.featuresStr.split(',').map(s => s.trim()).filter(Boolean);
      const payload = {
        chinese_name: this.form.chinese_name,
        latin_name: this.form.latin_name,
        features: features.length > 0 ? features : ['无明显特征'],
        category: this.categories[this.catIndex].value,
        protection_level: this.form.protection_level,
        observation_season: this.form.observation_season,
        fun_fact: this.form.fun_fact,
        rarity: this.form.rarity,
        user_id: this.userId
      };

      try {
        const response = await uni.request({
          url: `${API_BASE}/species/register`,
          method: 'POST',
          data: payload
        });
        const res = Array.isArray(response) ? response[1] : response;
        
        if (res && res.data && res.data.success) {
          uni.showToast({ title: '记录成功，正在生成...', icon: 'none' });
          const registerResult = res.data.data || {};
          await this.generateCard({ ...payload, card_id: registerResult.card_id || '' });
        } else {
          uni.showToast({ title: res?.data?.error?.message || '记录失败', icon: 'none' });
        }
      } catch (e) {
        uni.showToast({ title: '网络错误', icon: 'none' });
      } finally {
        this.isSubmitting = false;
      }
    },
    async generateCard(species) {
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/generate-card`,
          method: 'POST',
          data: {
            card_id: species.card_id || "",
            chinese_name: species.chinese_name,
            latin_name: species.latin_name,
            features: species.features || ['未知'],
            category: species.category || "plant",
            habitat: species.habitat || "",
            observation_season: species.observation_season || "",
            protection_level: species.protection_level || "",
            fun_fact: species.fun_fact || "",
            rarity: species.rarity || 3
          }
        });
        const res = Array.isArray(response) ? response[1] : response;
        if (res && res.data && res.data.success) {
          const result = res.data.data || {};
          species.image_path = result.image_path || '';
          
          // Switch to library and open detail or just switch to library
          uni.switchTab({ url: '/pages/index/index' });
          uni.showToast({ title: '记录完成并结卡', icon: 'success' });
          this.form = this.getInitialForm(); // reset
        }
      } catch (e) {}
    }
  }
}
</script>

<style lang="scss">
page { background: #FFFFFF; }
.container { padding-bottom: 90px; }
.header { padding: 30px 20px 20px; }
.title { font-size: 24px; font-weight: bold; color: #111827; }
.subtitle { font-size: 14px; color: #6B7280; margin-top: 5px; }

.form-container { padding: 0 20px; }
.form-item { margin-bottom: 20px; }
.label { display: block; font-size: 14px; color: #374151; margin-bottom: 8px; font-weight: 500; }
.input, .picker, .textarea { background: #F9FAFB; border: 1px solid #E5E7EB; padding: 12px 16px; border-radius: 12px; font-size: 15px; }
.textarea { width: auto; min-height: 80px; }

.footer {
  position: fixed; bottom: 0; left: 0; right: 0; padding: 15px 20px;
  background: white; border-top: 1px solid #F3F4F6;
  padding-bottom: env(safe-area-inset-bottom);
}
.submit-btn { background: #059669; color: white; text-align: center; padding: 16px; border-radius: 16px; font-size: 16px; font-weight: 600; }
.submit-btn.disabled { opacity: 0.6; }
</style>
