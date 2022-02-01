import config
import torch
import torch.optim as optim
import torchvision
import time

from torch.utils.tensorboard import SummaryWriter
from torch.utils.data import Dataset, DataLoader

from model_resnet import YoloV3
from dataloader import YoloDataset
from loss import YoloLoss
from torchvision_utils import draw_bounding_boxes

from utils import time_function
from utils import check_class_accuracy
from utils import get_evaluation_bboxes
from utils import mean_average_precision
from utils import save_checkpoint
from utils import load_checkpoint
from utils import draw_y_on_x
from utils import draw_yp_on_x


def main():

    # Data loading
    train_csv_path = config.DATASET + "100examples.csv"
    test_csv_path = config.DATASET + "100examples.csv"
    train_dataset = YoloDataset(train_csv_path, transforms=config.max_transforms, Scale=config.Scale, image_dir=config.IMG_DIR, label_dir=config.LABEL_DIR, anchor_boxes=config.ANCHORS, number_of_anchors=3, number_of_scales=3, ignore_iou_threshold=0.5, num_anchors_per_scale=3)
    test_dataset = YoloDataset(test_csv_path, transforms=config.max_transforms, Scale=config.Scale, image_dir=config.IMG_DIR, label_dir=config.LABEL_DIR, anchor_boxes=config.ANCHORS, number_of_anchors=3, number_of_scales=3, ignore_iou_threshold=0.5, num_anchors_per_scale=3)
    train_loader = DataLoader(dataset=train_dataset, batch_size=config.BATCH_SIZE, num_workers=config.NUM_WORKERS, pin_memory=config.PIN_MEMORY, shuffle=False, drop_last=True)
    test_loader = DataLoader(dataset=test_dataset, batch_size=config.BATCH_SIZE, num_workers=config.NUM_WORKERS, pin_memory=config.PIN_MEMORY, shuffle=False, drop_last=True)

    # Model
    model = YoloV3(num_classes=config.C).to(device=config.DEVICE)
    optimizer = optim.Adam(model.parameters(), lr=config.LEARNING_RATE, weight_decay=config.WEIGHT_DECAY)
    loss_function = YoloLoss()
    scalar = torch.cuda.amp.GradScaler()

    # Miscellaneous
    scaled_anchors = (torch.tensor(config.ANCHORS) * torch.tensor(config.Scale).unsqueeze(1).unsqueeze(1).repeat(1, 3, 2)).to(config.DEVICE)
    writer = SummaryWriter()
    current_time = time.time()

    # Loading previously saved model weights
    if config.LOAD_MODEL:
        load_checkpoint(config.CHECKPOINT_FILE, model, optimizer, config.LEARNING_RATE)

    for batch, (x, y) in enumerate(test_loader):
        model.eval()
        with torch.no_grad():
            x_gpu = x.float()
            x_gpu = x_gpu.to(config.DEVICE)
            yp = model(x_gpu)
            yp = [yp[0].to('cpu'), yp[1].to('cpu'), yp[2].to('cpu')]
        x = draw_yp_on_x(x, yp, probability_threshold=0.5, anchors=config.ANCHORS)
        x = draw_y_on_x(x, y)
        grid = torchvision.utils.make_grid(x, nrow=4)
        writer.add_image("yp_on_x", grid, global_step=batch)


if __name__ == "__main__":
    main()
