from loader import load, dataset_summary
from analysis import run_all
from figures import save_all

def main():
    # Load dataset
    df_all, df, df_mechs = load()

    # Print summary
    summary = dataset_summary(df_all, df)

    print("\nDataset Summary")
    print("----------------")
    for k, v in summary.items():
        print(f"{k}: {v}")

    # Run analysis
    tables = run_all(df_all, df, df_mechs, save=True)

    # Generate figures
    save_all(tables, save=True)

    print("\nDone.")
    print("Tables saved to outputs/tables/")
    print("Figures saved to outputs/figures/")

if __name__ == "__main__":
    main()