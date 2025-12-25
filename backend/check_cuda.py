import torch

def check_cuda():
    print("=== CUDA CHECK ===")

    print(f"PyTorch version : {torch.__version__}")
    print(f"CUDA available  : {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"CUDA version    : {torch.version.cuda}")
        print(f"GPU count       : {torch.cuda.device_count()}")

        for i in range(torch.cuda.device_count()):
            print(f"\nGPU #{i}")
            print(f"Name            : {torch.cuda.get_device_name(i)}")
            print(f"Capability      : {torch.cuda.get_device_capability(i)}")
            print(f"Total Memory    : {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
    else:
        print("❌ CUDA tidak terdeteksi, PyTorch menggunakan CPU")

    print("\n=== TEST TENSOR ===")
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        x = torch.rand(1000, 1000, device=device)
        y = torch.mm(x, x)
        print(f"Tensor test berhasil di device: {device.upper()}")
    except Exception as e:
        print("❌ Tensor test gagal:", e)


if __name__ == "__main__":
    check_cuda()
