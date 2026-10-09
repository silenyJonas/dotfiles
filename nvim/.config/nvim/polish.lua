-- File: vs_complete.lua
-- Kompletní Visual Studio (Windows) Keymap styl pro Neovim/Neovide

-- Pomocná funkce pro zjednodušení mapování kláves
local function map(mode, lhs, rhs, opts)
  local options = { noremap = true, silent = true }
  if opts then
    options = vim.tbl_extend("force", options, opts)
  end
  vim.keymap.set(mode, lhs, rhs, options)
end

----------------------------------------------------------------------
-- == ZÁKLADNÍ WINDOWS MANIPULACE S TEXTEM (Ctrl+C/V/X/Z) ==
----------------------------------------------------------------------

-- Ctrl+C: Kopírovat označený text do systémové schránky
-- V Normálním režimu to ruší příkaz, ale ve VS stylu je to kopírování.
map({ "n", "v" }, "<C-c>", '"+y') 

-- Ctrl+X: Vyjmout označený text (Visual Mode) do systémové schránky
map("v", "<C-x>", '"+d')

-- Ctrl+V: Vložit text ze systémové schránky
-- V Normálním režimu (n) a Vizuálním režimu (v)
map({ "n", "v" }, "<C-v>", '"+p')
-- V Vkládacím režimu (i)
map("i", "<C-v>", "<C-r>+") 

-- Ctrl+Z: Zpět (Undo)
map("n", "<C-z>", "u")
-- Ctrl+Y: Znovu (Redo) - VS styl
map("n", "<C-y>", "<C-r>")

----------------------------------------------------------------------
-- == VÝBĚR TEXTU (SHIFT + ŠIPKY) ==
----------------------------------------------------------------------

-- POZNÁMKA: V Normálním režimu se nejprve vstoupí do Vizuálního režimu.
-- Ctrl+B pro otevření/zavření Nvim-Tree (stejně jako ve VS Code)
vim.keymap.set('n', '<C-b>', ':NvimTreeToggle<CR>', { noremap = true, silent = true })

-- Shift + Šipka vpravo/vlevo: Výběr po znacích
map("n", "<S-Right>", "vl")
map("n", "<S-Left>", "vh")

-- Shift + Šipka nahoru/dolů: Výběr po řádcích
map("n", "<S-Down>", "vj")
map("n", "<S-Up>", "vk")

-- Ctrl + Shift + Šipka vpravo/vlevo: Výběr po slovech (Word Selection)
map("n", "<C-S-Right>", "vw")
map("n", "<C-S-Left>", "vb")

-- Ctrl + Shift + Šipka nahoru/dolů: Pohyb celého řádku (Move Line)
-- Klasická VS funkce pro posun řádku
map("n", "<C-S-Up>", ":m .-2<CR>")
map("n", "<C-S-Down>", ":m .+1<CR>")

----------------------------------------------------------------------
-- == PŘÍKAZY PRO ÚPRAVU A VYHLEDÁVÁNÍ (doplnění z předchozího kroku) ==
----------------------------------------------------------------------

-- Ctrl+F: Hledat v souboru (Find) - Spustí Neovim hledání (/)
map("n", "<C-f>", "/<C-r><C-w>")

-- Ctrl+S: Uložit soubor (Save)
map("n", "<C-s>", ":w<CR>")

-- F12: Jít na definici (Go to Definition)
map("n", "<F12>", ":lua vim.lsp.buf.definition()<CR>")

-- F5: Spustit/Pokračovat ladění (Start/Continue Debugging)
map("n", "<F5>", "<cmd>DapContinue<CR>")

-- Ctrl+Tab: Přepnout na další buffer
map("n", "<C-Tab>", ":bn<CR>")
