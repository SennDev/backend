import io
import pandas as pd
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from .models import Dataset
from .serializers import DatasetSerializer

class DatasetViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all().order_by('-uploaded_at')
    serializer_class = DatasetSerializer
    parser_classes = (MultiPartParser, FormParser)

def perform_create(self, serializer):
    file = self.request.FILES.get('file')
    if not file:
        raise ValidationError("No file uploaded")
    serializer.save(name=file.name, csv_file=file)


def load_df_from_dataset(dataset: Dataset):
    f = dataset.csv_file
    try:
        return pd.read_csv(f.path)
    except Exception:
        f.open('rb')
        content = f.read()
        f.close()
        return pd.read_csv(io.BytesIO(content))

class MetricsView(APIView):
    def get(self, request, pk):
        ds = get_object_or_404(Dataset, pk=pk)
        df = load_df_from_dataset(ds)

        rows = len(df)
        columns = len(df.columns)
        types = {col: str(df[col].dtype) for col in df.columns}
        nulls = df.isnull().sum().to_dict()
        duplicates_count = int(df.duplicated().sum())

        return Response({
            'dataset_id': ds.id,
            'name': ds.name,
            'rows': rows,
            'columns': columns,
            'nulls_per_column': nulls,
            'duplicates_count': duplicates_count,
            'types': types,
        })

class ColumnDistributionView(APIView):
    def get(self, request, pk, column):
        bins = int(request.GET.get('bins', 10))
        ds = get_object_or_404(Dataset, pk=pk)
        df = load_df_from_dataset(ds)

        if column not in df.columns:
            return Response({'detail': f'Column {column} not found'}, status=status.HTTP_404_NOT_FOUND)

        ser = df[column].dropna()

        # Intentar histograma numérico; si no, categorías
        try:
            ser_num = pd.to_numeric(ser, errors='coerce').dropna()
            if len(ser_num) == 0:
                raise ValueError("no numeric")
            counts = pd.cut(ser_num, bins=bins)
            hist = ser_num.groupby(counts).size().reset_index(name='count')

            bins_out = []
            for _, row in hist.iterrows():
                left = row[counts.name].left
                right = row[counts.name].right
                bins_out.append({'bin': f'{left:.2f}-{right:.2f}', 'count': int(row['count'])})

            quantiles = {
                'min': float(ser_num.min()),
                'q1': float(ser_num.quantile(0.25)),
                'median': float(ser_num.median()),
                'q3': float(ser_num.quantile(0.75)),
                'max': float(ser_num.max()),
            }
            return Response({'column': column, 'type': 'histogram', 'bins': bins_out, 'quantiles': quantiles})
        except Exception:
            vc = ser.astype(str).value_counts().head(50)
            bins_out = [{'bin': str(idx), 'count': int(cnt)} for idx, cnt in vc.items()]
            return Response({'column': column, 'type': 'categorical', 'bins': bins_out, 'quantiles': {}})
