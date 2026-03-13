<template>
  <view class="container">
    <view class="card-preview-section" v-if="cardImageUrl">
      <view class="card-preview-box" @click="previewCard">
        <image class="card-preview-image" :src="cardImageUrl" mode="widthFix"></image>
      </view>
      <view class="preview-action" @click="previewCard">查看大图</view>
    </view>

    <view class="form-container">
      <view class="form-item">
        <text class="label">收件人邮箱</text>
        <input class="input" v-model="form.to_email" placeholder="输入邮箱地址" type="text" />
      </view>
      <view class="form-item">
        <text class="label">邮件主题（选填）</text>
        <input class="input" v-model="form.email_subject" placeholder="不填则使用默认主题" />
      </view>
      <view class="form-item">
        <text class="label">附加想说的话（选填）</text>
        <textarea class="textarea" v-model="form.email_body" placeholder="说点什么吧..." />
      </view>
    </view>

    <view class="footer">
      <view class="btn primary-btn" :class="{disabled: isSubmitting}" @click="sendEmail">
        {{ isSubmitting ? '发送中...' : '发送邮件' }}
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
      cardId: '',
      speciesName: '物种',
      cardImageUrl: '',
      isSubmitting: false,
      form: {
        to_email: '13640292241@qq.com', // default from gateway
        email_subject: '',
        email_body: ''
      }
    }
  },
  onLoad(options) {
    if (options.card_id) this.cardId = options.card_id;
    if (options.chinese_name) this.speciesName = decodeURIComponent(options.chinese_name);
    if (this.cardId) this.loadCardDetail();
  },
  methods: {
    async loadCardDetail() {
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/${encodeURIComponent(this.cardId)}`,
          method: 'GET'
        });
        const res = Array.isArray(response) ? response[1] : response;
        if (res?.data?.success) {
          const detail = res.data.data || {};
          this.cardImageUrl = this.toImageUrl(detail.card_image_path || detail.image_path || '');
          if (detail.chinese_name) this.speciesName = detail.chinese_name;
        }
      } catch (e) {
        console.error(e);
      }
    },
    previewCard() {
      if (!this.cardImageUrl) return;
      uni.previewImage({ urls: [this.cardImageUrl] });
    },
    toImageUrl(imagePath) {
      if (!imagePath) return '';
      if (/^https?:\/\//.test(imagePath)) return imagePath;
      const normalized = String(imagePath).replace(/\\/g, '/').replace(/^\/+/, '');
      return `${SERVER_BASE}/${normalized}`;
    },
    async sendEmail() {
      if (!this.form.to_email) {
        uni.showToast({ title: '请填写收件人邮箱', icon: 'none' });
        return;
      }
      if (!this.cardId) {
        uni.showToast({ title: '缺少卡片ID无法发送', icon: 'none' });
        return;
      }

      this.isSubmitting = true;
      try {
        const response = await uni.request({
          url: `${API_BASE}/species/${this.cardId}/email`,
          method: 'POST',
          data: {
            to_email: this.form.to_email,
            email_subject: this.form.email_subject || undefined,
            email_body: this.form.email_body || undefined
          }
        });
        const res = Array.isArray(response) ? response[1] : response;
        if (res && res.data && res.data.success) {
          uni.showToast({ title: '邮件发送成功', icon: 'success' });
          setTimeout(() => {
            uni.navigateBack();
          }, 1500);
        } else {
          uni.showToast({ title: res?.data?.error?.message || '发送失败', icon: 'none' });
        }
      } catch (e) {
        uni.showToast({ title: '网络错误', icon: 'none' });
      } finally {
        this.isSubmitting = false;
      }
    }
  }
}
</script>

<style lang="scss">
page { background: #FFFFFF; }
.header { padding: 40px 20px 20px; }
.title { font-size: 24px; font-weight: bold; color: #111827; }
.subtitle { font-size: 14px; color: #6B7280; margin-top: 5px; }
.card-preview-section { padding: 0 20px 20px; }
.section-title { font-size: 16px; font-weight: bold; color: #111827; margin-bottom: 12px; display: block; }
.card-preview-box { background: #F9FAFB; border-radius: 16px; overflow: hidden; }
.card-preview-image { width: 100%; display: block; }
.preview-action { margin-top: 10px; text-align: center; color: #059669; font-size: 14px; font-weight: 600; }

.form-container { padding: 20px; }
.form-item { margin-bottom: 20px; }
.label { display: block; font-size: 14px; color: #374151; margin-bottom: 8px; font-weight: 500; }
.input, .textarea { background: #F9FAFB; border: 1px solid #E5E7EB; padding: 12px 16px; border-radius: 12px; font-size: 15px; }
.textarea { width: auto; min-height: 100px; }

.footer {
  padding: 30px 20px;
}
.btn { text-align: center; padding: 14px; border-radius: 12px; font-weight: 600; font-size: 16px; }
.primary-btn { background: #059669; color: white; }
.primary-btn.disabled { opacity: 0.6; }
</style>
