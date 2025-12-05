import org.biojava.nbio.core.sequence.ProteinSequence;
import org.biojava.nbio.core.sequence.io.FastaReaderHelper;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.*;

public class Main {
    public static void main(String[] args) throws Exception {
        LinkedHashMap<String, ProteinSequence> resp = null;
        try {
            resp = FastaReaderHelper.readFastaProteinSequence(new File("uniprot_sprot.fasta"));
            ArrayList<String> allID = new ArrayList<>();
            resp.entrySet().forEach(e -> allID.add(e.getKey()));
            Collections.shuffle(allID);
            FileWriter sb = new FileWriter(new File("randomPeptide.fasta"));
            for (int i = 0; i < 3000; i++) {
                ProteinSequence protein = resp.get(allID.get(i));
                if (protein.getSequenceAsString().length() > 200) {
                    int min = 10;
                    int max = 30;
                    Random random = new Random();
                    int peptideSize = random.nextInt(max - min + 1) + min;
                    String sequencia = protein.getSequenceAsString();
                    int startIndex = random.nextInt(sequencia.length() - peptideSize + 1);

                    int endIndex = startIndex + peptideSize;
                    String randomPeptide = sequencia.substring(startIndex, endIndex);
                    sb.append(">");
                    sb.append(allID.get(i));
                    sb.append("\n");
                    sb.append(randomPeptide);
                    sb.append("\n");
                }
            }
        } catch (IOException ex) {
            ex.printStackTrace();
            System.exit(1);
        }
    }
}