using System.Windows;
using StarSaviorTool.ViewModels;

namespace StarSaviorTool
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            Loaded += async (_, _) =>
            {
                if (DataContext is MainViewModel vm)
                {
                    await vm.InitializeAsync();
                }
            };
        }
    }
}