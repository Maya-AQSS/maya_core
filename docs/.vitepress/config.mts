import { defineConfig } from 'vitepress';
import { withMermaid } from 'vitepress-plugin-mermaid';  // Necesario para diagramas C4/Mermaid

export default withMermaid(
  defineConfig({
    title: "Maya | Core",
    description: "Módulo Odoo (core) para la gestión interna del Centro Específico de Educación a Distancia de la Comunidad Valenciana - CEEDCV",
    lang: 'es-ES',

    // Para GitHub Pages
    base: '/maya_core/',
    srcDir: './src',

    ignoreDeadLinks: true,

    mermaid: {
      theme: 'dark'
    },

    themeConfig: {
      nav: [
        { text: 'Inicio', link: '/' },
        { text: 'Guía de Usuario', link: '/user/getting-started' },
        { text: 'Guía de Desarrollo', link: '/dev/overview' },
        { 
          text: 'v0.1.0',
          items: [
            { text: 'Changelog', link: '/changelog' },
          ]
        }
      ],
      sidebar: {
        '/user/': [
          {
            text: 'Guía de Usuario',
            items: [
              { text: 'Comenzar', link: '/user/getting-started' },
              { text: 'Instalación', link: '/user/installation' },
            ]
          },
        ],       
        '/dev/': [
          {
            text: 'Guía de Desarrollo',
            items: [
              { text: 'Visión General', link: '/dev/overview' },
              { text: 'Entorno de Desarrollo', link: '/dev/setup' },
              { text: 'Estructura del Proyecto', link: '/dev/structure' },
              { text: 'Arquitectura', link: '/dev/architecture' },
              { text: 'Flujo de Trabajo', link: '/dev/workflow' },
              { text: 'Épicas', link: '/dev/epics' }
            ]
          },
        ],
      },
      socialLinks: [
        { icon: 'github', link: 'https://github.com/Maya-AQSS/maya_core' }
      ],

      footer: {
        message: 'Maya | Core — Módulo principal de Odoo para la gestión interna del CEEDCV',
        copyright: 'Copyright © 2026'
      },

      search: {
        provider: 'local'
      },

      editLink: {
        pattern: 'https://github.com/Maya-AQSS/maya_core/edit/main/docs/:path',
        text: 'Editar esta página en GitHub'
      },

      lastUpdated: {
        text: 'Última actualización',
        formatOptions: {
          dateStyle: 'short',
          timeStyle: 'short'
        }
      }
    }
  })
)
