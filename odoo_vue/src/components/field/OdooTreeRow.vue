<template>
  <div class="vux-1px-t">
    <swipeout>
      <div>
        <div class="weui-panel__hd" v-if="header" @click="onClickHeader" v-html="header">
          <slot name="header"></slot>
        </div>
        <div class="weui-panel__bd">
          <div ame="body">
            <div v-for="(item, index) in list_locate">
              <swipeout-item transition-mode="follow">
                <div slot="right-menu" v-if="showOperation">
                  <swipeout-button @click.native="onButtonClick('edit', item, index)" type="primary">{{'编辑'}}
                  </swipeout-button>
                  <swipeout-button @click.native="onButtonClick('delete', item, index)" type="warn">{{'删除'}}
                  </swipeout-button>
                </div>
                <div slot="content" class="demo-content vux-1px-t" @click.prevent="onItemClick(item)">
                  <template v-if="item.title">
                    <h4 class="weui-media-box__title">{{item.title}}</h4>
                  </template>
                  <ul class="weui-media-box__info">
                    <template v-for="(field) in item.meta">
                      <template v-if="!field.invisible || !field.is_show_form_tree">
                        <template
                          v-if="['char', 'date', 'datetime', 'integer', 'float'].indexOf(field.type)>=0">
                          <li class="weui-media-box__info__meta">{{field.title}}: <span class="line_color_value">{{field.value}}</span></li>
                        </template>
                        <template
                          v-if="['many2one'].indexOf(field.type)>=0">
                          <li class="weui-media-box__info__meta">{{field.title}}: <span class="line_color_value">{{ field.options ? field.options[0].value: ''}}</span></li>
                        </template>
                        <template v-else-if="['boolean'].indexOf(field.type) >= 0">
                          <li class="weui-media-box__info__meta" v-if="field.value">{{field.title}}:
                            <icon type="success"></icon>
                          </li>
                          <li class="weui-media-box__info__meta" v-else>{{field.title}}:
                            <icon type="cancel"></icon>
                          </li>
                        </template>
                        <template v-else-if="['selection'].indexOf(field.type) >= 0">
                          <li class="weui-media-box__info__meta" v-if="field.value">{{field.title}}:
                            <span class="line_color_value">{{field.options?field.options[0].value:''}}</span>
                          </li>
                        </template>
                      </template>
                    </template>
                  </ul>
                </div>
              </swipeout-item>
            </div>
          </div>
        </div>
        <div class="weui-panel__ft">
          <a
            class="weui-cell weui-cell_access weui-cell_link"
            v-if="footer && footer.title"
            @click.prevent="onClickFooter">
            <div class="weui-cell__bd" v-html="footer.title"></div>
          </a>
        </div>
      </div>
    </swipeout>
    <div v-transfer-dom>
      <popup v-model="showForm" height="100%" position="bottom" :show-mask="true">
        <div class="popup0">
          <group>
            <treeForm :allFormData.sync="allFormData" :isEdit="isEdit"
                      :model="model" :id="id" @save="addNewRecord" @cancel="cancelAdd"></treeForm>
          </group>
        </div>
      </popup>
    </div>
  </div>
</template>

<script>
  import treeForm from './OdooTreeForm.vue'
  import {Group, Icon, TransferDom, Swipeout, SwipeoutItem, SwipeoutButton, Popup} from 'vux'
  export default {
    name: 'TreeRow',
    components: {
      Popup,
      Icon,
      treeForm,
      Group,
      Swipeout,
      SwipeoutItem,
      SwipeoutButton
    },
    directives: {
      TransferDom
    },
    props: ['header', 'footer', 'list', 'model', 'viewId', 'recordField', 'context', 'showOperation'],
    data: function () {
      return {
        showForm: false,
        id: '',
        isEdit: false,
        allFormData: {},
        menu: [],
        editIndex: 0
      }
    },
    computed: {
      list_locate: {
        get: function () {
          return this.list || []
        },
        set: function (v) {
          this.$emit('update:list', v)
        }
      }
    },
    watch: {
      list_locate: {
        handler: function (val, oldVal) {
          this.$emit('update:list', val)
        },
        deep: true
      }
    },
    methods: {
      onButtonClick: function (event, item, index) {
        let self = this
        if (event === 'edit') {
          if (!self.recordField) {
            self.$router.push({
              name: 'newForm',
              params: {
                id: item.id,
                model: self.model,
                viewId: self.viewId
              }
            })
          } else {
            self.allFormData = {
              fieldVals: item.meta,
              id: item.id
            }
            self.isEdit = true
            self.editIndex = index
            self.showForm = true
          }
        } else if (event === 'delete') {
          self.delete(item, index)
        }
      },
      delete: function (item, index) {
        let self = this
        if (!self.recordField) {
          self.$http.get('/odoo/mobile/button/method', {
            params: {
              method: 'unlink',
              model: self.model,
              ids: item.id
            }
          }).then(function (response) {
            if (response.data.success) {
              self.list_locate.splice(index, index + 1)
            } else {
              self.$emit('error-toast', {toastType: 'warn', toastMsg: response.data.errMsg, toastShow: true})
            }
          }).catch(function () {

          })
        } else {
          self.list_locate.splice(index, index + 1)
        }
      },
      addNewRecord: function (newRecord) {
        let self = this
        if (!self.isEdit) {
          this.list_locate.push({meta: newRecord.fieldVals, id: newRecord.id || 0, title: '新添加'})
        } else {
          this.list_locate[self.editIndex] = { meta: newRecord.fieldVals, id: newRecord.id || 0, title: '本条修改记录' }
        }
        this.allFormData = {}
        this.showForm = false
      },
      cancelAdd: function (newRecord) {
        this.allFormData = {}
        this.showForm = false
      },
      onClickFooter: function () {
        let self = this
        self.isEdit = false
        self.allFormData = {fieldVals: JSON.parse(JSON.stringify(self.recordField)), id: 0}
        self.showForm = true
      },
      onClickHeader: function () {
        this.$emit('on-click-header')
      },
      onItemClick: function (item) {
        this.$emit('on-click-tree-item', item)
      },
      get_form_data: function () {
        let self = this
        self.$http.get('/odoo/mobile/form/new/data', {model: this.model, id: this.recordId}).then(function (response) {
          self.allFormData = response.data
        }).catch(function (error) {
          alert(error)
        })
      }
    }
  }
</script>

<style lang="less">
  @import '~vux/src/styles/weui/widget/weui_cell/weui_cell_global';
  @import '~vux/src/styles/weui/widget/weui_cell/weui_access';
  @import '~vux/src/styles/weui/widget/weui_panel/weui_panel';
  @import '~vux/src/styles/weui/widget/weui_media_box/weui_media_box';

  /*demo-content {*/
  /*padding: 0px 10px 10px 10px;*/
  /*}*/
  .weui-media-box__title {
    font-size: 15px;
    color: #080209;
    padding: 5px 0px 0px 10px;
  }
  .weui-panel__hd {
    color: #080209;
  }
  .weui-media-box__info {
    padding: 0px 0px 10px 10px;
    margin-top: 8px;

  }
  .weui-media-box__info__meta {
    color: #92888f
  }
  .line_color_value {
    color: #080209
  }
</style>
