-- Autocommand pro automatické spuštění Neo-tree
vim.api.nvim_create_autocmd("VimEnter", {
  callback = function()
    local dir = vim.fn.argv(0)
    -- Spustí Neo-tree jako sidebar, pokud otevřeš složku (použiješ nvim .)
    if vim.fn.isdirectory(dir) == 1 and dir ~= "" then
      vim.cmd.Neotree "toggle"
    end
  end,
})

return {} -- Ujisti se, že tento řádek tam je!
