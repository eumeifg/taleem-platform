module.exports = {
  devServer: {
    proxy: 'http://localhost:3001',
  },
  chainWebpack: (config) => {
    config.plugins.delete('prefetch')

    config.module.rules.delete('scss')
    config.module.rule('scss')
      .test(/\.scss$/)
      .use('style-loader')
      .loader('style-loader')
      .options({
        insert: (elem) => {
          if (window.__appendStyle__) {
            window.__appendStyle__(elem)
          } else {
            window.__stylesToAppend__ = [
              ...(window.__stylesToAppend__ || []),
              elem,
            ]
          }
        },
      })
    config.module.rule('scss')
      .test(/\.scss$/)
      .use('css-loader')
      .loader('css-loader')
    config.module.rule('scss')
      .test(/\.scss$/)
      .use('sass-loader')
      .loader('sass-loader')

    config.module.rules.delete('css')
    config.module.rule('css')
      .test(/\.css$/)
      .use('style-loader')
      .loader('style-loader')
      .options({
        insert: (elem) => {
          if (window.__appendStyle__) {
            window.__appendStyle__(elem)
          } else {
            window.__stylesToAppend__ = [
              ...(window.__stylesToAppend__ || []),
              elem
            ]
          }
        },
      })
    config.module.rule('css')
      .test(/\.css$/)
      .use('css-loader')
      .loader('css-loader')
  },
}
