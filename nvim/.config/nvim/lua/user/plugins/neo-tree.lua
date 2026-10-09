return {
  -- Konfigurace pro Neo-tree
  {
    "nvim-neo-tree/neo-tree.nvim",
    opts = {
      window = {
        position = "left",
        width = 30,
        -- TATO VOLBA ZABRÁNÍ ZAVŘENÍ PO OTEVŘENÍ SOUBORU
        close_if_file_opened = false, 
      },
      filesystem = {
        -- Tato volba je klíčová, aby se strom otevřel hned
        auto_open_if_empty = true, 
        follow_current_file = {
          enabled = true,
        },
      },
      -- TOTO JE TAKÉ DŮLEŽITÉ: Ujisti se, že máš aktivní mód "filesystem"
      sources = { "filesystem", "buffers", "git_status" }, 
    },
  },
}
