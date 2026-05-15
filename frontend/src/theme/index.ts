import type { ThemeConfig } from 'antd';

/**
 * Vercel-inspired Ant Design theme
 * Maps UI_DESIGN.md tokens to Ant Design v5 theme config.
 */
export const vercelTheme: ThemeConfig = {
  token: {
    // ── Brand / Primary ──
    colorPrimary: '#171717', // ink — the single primary CTA color
    colorLink: '#0070f3', // link blue
    colorLinkHover: '#0761d1', // link-deep
    colorSuccess: '#0070f3',
    colorError: '#ee0000',
    colorWarning: '#f5a623',
    colorInfo: '#0070f3',

    // ── Surfaces ──
    colorBgLayout: '#fafafa', // canvas-soft
    colorBgContainer: '#ffffff', // canvas
    colorBgElevated: '#ffffff', // canvas (modals, dropdowns)
    colorBorder: '#ebebeb', // hairline
    colorBorderSecondary: '#ebebeb',

    // ── Text ──
    colorText: '#171717', // ink
    colorTextSecondary: '#4d4d4d', // body
    colorTextTertiary: '#888888', // mute
    colorTextQuaternary: '#a1a1a1',
    colorWhite: '#ffffff',

    // ── Border Radius ──
    borderRadius: 6, // rounded.sm (6px) — in-app base
    borderRadiusLG: 8, // rounded.md (8px) — cards
    borderRadiusSM: 4, // rounded.xs (4px)
    borderRadiusXS: 2,

    // ── Font ──
    fontFamily: "Inter, system-ui, -apple-system, sans-serif",
    fontSize: 14, // body-sm base
    fontSizeHeading1: 32, // display-lg
    fontSizeHeading2: 24, // display-md
    fontSizeHeading3: 20, // display-sm
    fontSizeHeading4: 16, // body-md-strong
    fontSizeHeading5: 14, // body-sm-strong

    // ── Line Height ──
    lineHeight: 1.4286, // 20px / 14px
    lineHeightHeading1: 1.25, // 40px / 32px
    lineHeightHeading2: 1.3333, // 32px / 24px
    lineHeightHeading3: 1.4, // 28px / 20px
    lineHeightHeading4: 1.5, // 24px / 16px
    lineHeightHeading5: 1.4286, // 20px / 14px

    // ── Spacing (4px base) ──
    marginXXS: 4,
    marginXS: 8,
    marginSM: 12,
    margin: 16,
    marginMD: 16,
    marginLG: 24,
    marginXL: 32,
    marginXXL: 40,
    paddingXXS: 4,
    paddingXS: 8,
    paddingSM: 12,
    padding: 16,
    paddingMD: 16,
    paddingLG: 24,
    paddingXL: 32,

    // ── Shadow (Vercel-style stacked shadows) ──
    boxShadow: '0px 1px 1px rgba(0,0,0,0.05), 0px 2px 2px rgba(0,0,0,0.10)',
    boxShadowSecondary: '0px 2px 2px rgba(0,0,0,0.10), 0px 8px 16px -4px rgba(0,0,0,0.10)',
  },
  components: {
    Button: {
      borderRadius: 6, // rounded.sm for in-app buttons
      borderRadiusLG: 100, // rounded.pill for large/marketing buttons
      controlHeight: 32, // button-sm height (~32px)
      controlHeightLG: 40,
      fontWeight: 500, // button-md weight
      fontSize: 14, // button-md
      lineHeight: 1.4286, // 20px / 14px
      colorPrimary: '#171717', // ink bg
      colorPrimaryHover: '#000000',
      colorPrimaryActive: '#000000',
      defaultBorderColor: '#ebebeb',
      defaultColor: '#171717',
      defaultHoverBorderColor: '#a1a1a1',
      paddingContentHorizontal: 12, // padding.sm
      paddingContentHorizontalLG: 16, // padding.md
    },
    Card: {
      borderRadius: 8, // rounded.md
      boxShadow: '0px 1px 1px rgba(0,0,0,0.05), 0px 2px 2px rgba(0,0,0,0.10)',
      colorBorderSecondary: '#ebebeb',
      padding: 24, // spacing.lg
      paddingLG: 24,
      fontSize: 14,
      lineHeight: 1.4286,
    },
    Input: {
      borderRadius: 6, // rounded.sm
      controlHeight: 40, // form-input height
      controlHeightSM: 32, // form-input-sm
      controlHeightLG: 48, // form-input-lg
      colorBorder: '#ebebeb',
      hoverBorderColor: '#a1a1a1',
      activeBorderColor: '#171717',
      paddingInline: 12,
      paddingInlineSM: 12,
      fontSize: 14,
    },
    Select: {
      borderRadius: 6,
      controlHeight: 40,
      colorBorder: '#ebebeb',
      hoverBorderColor: '#a1a1a1',
    },
    Table: {
      borderRadius: 8,
      colorBorderSecondary: '#ebebeb',
      headerBg: '#fafafa', // canvas-soft
      headerColor: '#4d4d4d', // body
      headerFontSize: 12,
      rowHoverBg: '#f5f5f5', // canvas-soft-2
      fontSize: 14,
    },
    Tabs: {
      colorBorderSecondary: '#ebebeb',
      inkBarColor: '#171717',
      itemColor: '#4d4d4d',
      itemHoverColor: '#171717',
      itemActiveColor: '#171717',
      fontSize: 14,
    },
    Tag: {
      borderRadius: 100, // rounded.full
      fontSize: 12,
      lineHeight: 1.3333,
      paddingContentHorizontal: 8, // spacing.xs
    },
    Modal: {
      borderRadius: 12, // rounded.lg
      borderRadiusLG: 12,
      boxShadow: '0px 1px 1px rgba(0,0,0,0.05), 0px 8px 16px -4px rgba(0,0,0,0.10), 0px 24px 32px -8px rgba(0,0,0,0.15)',
    },
    Menu: {
      borderRadius: 6,
      itemBorderRadius: 6,
      itemColor: '#4d4d4d', // body
      itemHoverColor: '#171717', // ink
      itemSelectedColor: '#171717', // ink
      itemSelectedBg: '#f5f5f5', // canvas-soft-2
      itemActiveBg: '#f5f5f5',
      subMenuItemBg: 'transparent',
      groupTitleColor: '#888888',
      fontSize: 14,
      colorPrimary: '#171717',
      colorBgContainer: '#ffffff',
      popupBg: '#ffffff',
    },
    Layout: {
      headerBg: '#ffffff',
      headerPadding: '0 24px',
      siderBg: '#ffffff',
      bodyBg: '#fafafa', // canvas-soft
      footerBg: '#ffffff',
    },
    Dropdown: {
      borderRadius: 8,
      colorBorder: '#ebebeb',
    },
    Popconfirm: {
      borderRadius: 8,
    },
    Form: {
      labelColor: '#4d4d4d',
      labelFontSize: 14,
      verticalLabelPadding: '0 0 4px',
    },
    List: {
      fontSize: 14,
      colorBorder: '#ebebeb',
    },
    DatePicker: {
      borderRadius: 6,
      controlHeight: 40,
      colorBorder: '#ebebeb',
    },
    Switch: {
      colorPrimary: '#171717',
    },
    Radio: {
      colorPrimary: '#171717',
    },
    Checkbox: {
      colorPrimary: '#171717',
    },
    Badge: {
      borderRadius: 100,
    },
    Progress: {
      borderRadius: 100,
    },
    Spin: {
      colorPrimary: '#171717',
    },
    Segmented: {
      borderRadius: 6,
      itemSelectedBg: '#171717',
      itemSelectedColor: '#ffffff',
    },
  },
};
